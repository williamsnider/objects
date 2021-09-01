from copy import Error
import trimesh
import numpy as np
from objects.parameters import SAMPLING_DENSITY_V, SAMPLING_DENSITY_U, ORDER
from objects.utilities import open_uniform_knot_vector, calc_face_normals
import scipy
import networkx as nx
from splipy import BSplineBasis, Curve, Surface
from objects.utilities import (
    plot_projected_vertices_and_NNs,
    plot_projected_vertices_and_NNs_3D,
    plot_mesh_derivatives,
    plot_surface_linking_axial_components,
)


class Shape:
    def __init__(self, ac_list):

        self.ac_list = ac_list

    def check_inputs(self):

        assert type(self.ac_list) is list, "ac_list must be a list, even if it has just 1 ac."

    def fuse_meshes(self, parent_ac, child_ac):

        parent_mesh = parent_ac.mesh

        # Define functions to carry out fusion in steps

        def find_join_slice_along_child(parent_mesh, child_ac, num_steps_long_axis, num_steps_round_axis):
            """Find slice along the child that is just outside the parent_ac."""

            # TODO: Do these on a simpler mesh to go faster

            # num_steps_long_axis = 10  # Try 10 different slices (increasing distance from parent_mesh)
            # num_steps_round_axis = (
            #     6  # Test if N points along slice are outside mesh
            # )
            (us, vs) = child_ac.surface.start()
            (ue, ve) = child_ac.surface.end()
            u = np.linspace(us, ue, num_steps_round_axis, endpoint=False)
            v = np.linspace(vs, ve, num_steps_long_axis)
            verts_array = child_ac.surface(u, v)

            for slice_num, _ in enumerate(v):
                print(slice_num)
                points = verts_array[:, slice_num, :]

                points_outside_mesh = ~parent_mesh.contains(points)
                if np.all(points_outside_mesh):  # All points outside
                    break

                if slice_num == len(v) - 1:
                    raise NotImplementedError

            slice_dist_approx = np.array(v[slice_num])  # Need to round this up to next highest value in actual v

            # Grab the full-size slice
            uu = SAMPLING_DENSITY_U
            vv = SAMPLING_DENSITY_V
            (us, vs) = child_ac.surface.start()
            (ue, ve) = child_ac.surface.end()
            v = np.linspace(vs, ve, vv)
            u = np.linspace(us, ue, uu, endpoint=False)
            slice_dist = v[v > slice_dist_approx][0]  # First value of v > slice_dist_approx
            full_slice = child_ac.surface(u, slice_dist)
            return full_slice, slice_dist, u, slice_dist_approx

        def project_child_slice_onto_parent_mesh(parent_mesh, child_ac, slice_dist):
            ### Expand this slice and project it onto the surface of the parent_mesh.

            TNB_current = np.stack(
                [
                    child_ac.T(slice_dist)[0],
                    child_ac.N(slice_dist)[0],
                    child_ac.B(slice_dist)[0],
                ],
                axis=0,
            )

            TNB_goal = np.array(
                [
                    [1, 0, 0],
                    [0, 1, 0],
                    [0, 0, 1],
                ]
            )

            R = np.linalg.inv(TNB_current) @ TNB_goal

            EXPANSION_FACTOR = 1.5
            center = child_ac.r(slice_dist)
            full_slice_rotated = ((full_slice - center) @ R * EXPANSION_FACTOR) + center
            mesh_verts_rotated = (parent_mesh.vertices - center) @ R + center

            # Remove x-axis
            full_slice_yz = np.squeeze(full_slice_rotated[:, :, 1:])
            mesh_verts_yz = mesh_verts_rotated[:, 1:]
            self.full_slice_yz = full_slice_yz
            self.mesh_verts_yz = mesh_verts_yz

            # Identify the 5 nearest neighbors for each point on the slice
            NUM_NN = 10
            tree = scipy.spatial.KDTree(mesh_verts_yz)
            dd, ii = tree.query(full_slice_yz, k=NUM_NN)

            # Choose the NN with the shortest distance in 3D
            mesh_points = mesh_verts_rotated[ii]
            slice_points = np.repeat(full_slice_rotated, NUM_NN, axis=1)
            dist = np.sqrt(np.sum((mesh_points - slice_points) ** 2, axis=2))
            min_idx = np.argmin(dist, axis=1)
            closest_NN = np.zeros((len(ii)), dtype="int")
            for i, _ in enumerate(closest_NN):
                closest_NN[i] = ii[i, min_idx[i]]

            _, unique_idx = np.unique(closest_NN, return_index=True)
            unique_NN = [closest_NN[i] for i in sorted(unique_idx)]
            unique_NN.append(unique_NN[0])  # Wrap starting point

            return unique_NN, closest_NN

        def find_path_between_projected_vertices(parent_mesh, unique_NN, closest_NN):
            # edges without duplication
            edges = parent_mesh.edges_unique

            # the actual length of each unique edge
            length = parent_mesh.edges_unique_length

            # create the graph with edge attributes for length
            g = nx.Graph()
            for edge, L in zip(edges, length):
                g.add_edge(*edge, length=L)

            # alternative method for weighted graph creation
            # you can also create the graph with from_edgelist and
            # a list comprehension, which is like 1.5x faster
            ga = nx.from_edgelist([(e[0], e[1], {"length": L}) for e, L in zip(edges, length)])

            # arbitrary indices of mesh.vertices to test with
            full_path = []
            for i in range(len(unique_NN)):
                print(i)
                start = unique_NN[i - 1]
                end = unique_NN[i]

                # run the shortest path query using length for edge weight
                new_path = nx.shortest_path(g, source=start, target=end, weight="length")

                # If this path overlaps previous path, remove the previous path
                repeated_verts = [p for p in new_path[1:] if p in full_path]
                if repeated_verts:

                    # Find the intermediate vertices (between the repeated) and cut them out

                    # Find the index of the last repeat in the new path
                    idx_path_repeat = -1
                    for r in repeated_verts:
                        idx = new_path.index(r)
                        if idx > idx_path_repeat:
                            idx_path_repeat = idx

                    # Find the index of the first repeat in the full path
                    idx_full_repeat = full_path.index(repeated_verts[0])  # Initilize
                    for r in repeated_verts:
                        idx = full_path.index(r)
                        if idx < idx_full_repeat:
                            idx_full_repeat = idx

                    # Get the vertices to be appended (skip the repeating ones)
                    try:
                        verts_to_append = new_path[idx_path_repeat + 1 :]
                    except:
                        verts_to_append = []

                    # Get the vertices for which we need to replace the assigned NN
                    NNs_to_replace = full_path[idx_full_repeat + 1 :] + new_path[:idx_path_repeat]
                    NN_replacement = full_path[idx_full_repeat]  # Just assign all

                    # Replace these NNs for the closest_NN array
                    for NN in NNs_to_replace:

                        closest_NN[closest_NN == NN] = NN_replacement
                else:
                    verts_to_append = new_path[1:]  # Don't duplicate first vert

                # Append to the full_path
                full_path.extend(verts_to_append)

            full_path.append(full_path[0])  # Add first element to end to close loop
            return full_path

        def create_surface_between_child_slice_and_parent_mesh(parent_mesh, child_ac, closest_NN, u):

            # Identify derivatives at points along parent_mesh. mesh
            p_V = parent_mesh.vertices[closest_NN]
            p_T = parent_mesh.vertices[closest_NN] - parent_mesh.vertices[np.roll(closest_NN, -1)]

            # Replace 0 values of tangent with last nonzero value
            for i, row in enumerate(p_T):

                if np.all(row == np.array([0.0, 0.0, 0.0])):

                    p_T[i] = p_T[i - 1]

            p_N = parent_mesh.vertex_normals[closest_NN]
            p_B = np.cross(p_N, p_T)
            p_B = p_B / np.linalg.norm(p_B, axis=1, keepdims=True)  # norm

            # Identify derivatives at points along child's full slice
            uuu = u
            c_V = child_ac.surface(uuu, slice_dist).squeeze()
            c_T = child_ac.surface.derivative(uuu, slice_dist, d=(0, 1)).squeeze()
            c_T = c_T / np.linalg.norm(c_T, axis=1, keepdims=True)

            # Create B-Spline Surface linking child slice and projection on parent

            # Inputs
            degree = ORDER - 1

            # Basis 1 - cross section
            # With >100 controlpoints, the curve essentially passes through the points, so when we go to switch this segment in, if we skip the first and last elements, I think it will work.
            num_cp_per_cross_section = c_V.shape[0]
            num_knots = num_cp_per_cross_section + ORDER + degree
            knot = np.linspace(0, 1, num_knots)
            basis1 = BSplineBasis(order=ORDER, knots=knot, periodic=1)

            curve = Curve(basis1, c_V, rational=False)

            # Basis 2 - along the major axis of the axial component
            num_rows = 4  # End termini + 2 intermediate points to determine slope
            knot = open_uniform_knot_vector(num_rows, ORDER)
            basis2 = BSplineBasis(order=ORDER, knots=knot, periodic=-1)

            # Controlpoints
            SCALE_FACTOR = 0.1
            cp = np.zeros([c_V.shape[0], 4, 3])
            cp[:, 0, :] = c_V
            cp[:, 1, :] = c_V - c_T * SCALE_FACTOR
            cp[:, 2, :] = p_V - p_B * SCALE_FACTOR
            cp[:, 3, :] = p_V
            cp = cp.reshape(num_rows * num_cp_per_cross_section, cp.shape[2], order="F")

            # Surface
            surface = Surface(basis1, basis2, cp, rational=False)
            self.surface = surface

            return surface, c_V, c_T

        def stitch_child_and_junction(child_ac, surface, slice_dist_approx):

            # Sample surface of junction
            uu = SAMPLING_DENSITY_U
            vv = SAMPLING_DENSITY_V
            (us, vs) = surface.start()
            (ue, ve) = surface.end()
            u = np.linspace(us, ue, uu, endpoint=False)
            v = np.linspace(vs, ve, vv)
            junction_verts_array = surface(u, v)

            # Get vertices of child, starting at the full_slice
            (us, vs) = child_ac.surface.start()
            (ue, ve) = child_ac.surface.end()
            v = np.linspace(vs, ve, vv)
            u = np.linspace(us, ue, uu, endpoint=False)
            v_slices = v[v > slice_dist_approx]
            child_verts_array = child_ac.surface(u, v_slices)
            child_mesh = None

            return child_mesh

        def remove_interior_vertices_from_parent(parent_mesh, full_path):

            # Strategy 1 - networkx
            parent_verts = parent_mesh.vertices

            # Find middle point (assume this is within region we want to cut out)
            centerpoint = parent_verts[full_path].mean(axis=0)

            # Find nearest neighbor of actual vertex to this centerpoint
            tree = scipy.spatial.KDTree(parent_verts)
            _, center_vert_idx = tree.query(centerpoint, k=1)

            edges = parent_mesh.edges_unique

            # create the graph
            g = nx.Graph()
            g.add_edges_from(edges)

            # Remove nodes comprising full_path
            g.remove_nodes_from(full_path)

            # Find vertices inside full_path
            interior = min(nx.connected_components(g), key=len)

            # Recreate graph, subtract out vertices inside full_path
            g = nx.Graph()
            g.add_edges_from(edges)
            g.remove_nodes_from(interior)

            # Confirm center_vert is NOT in subgraph
            assert (
                center_vert_idx not in g.nodes
            ), "Subgraph contains center_vert_idx - possibly chose the wrong subgraph."

            # Convert subgraph into a mesh
            verts = parent_mesh.vertices[g.nodes]

            # TODO: probably a faster way to do this w/o for loop
            face_indices = []
            for i, (v1, v2, v3) in enumerate(parent_mesh.faces):
                if v1 not in g.nodes:
                    continue
                elif v2 not in g.nodes:
                    continue
                elif v3 not in g.nodes:
                    continue
                else:
                    face_indices.append(i)

            # Renumber vertices in faces
            old_indices = list(g.nodes)
            new_indices = np.arange(0, len(g.nodes))
            renumber_dict = {o: n for o, n in zip(old_indices, new_indices)}
            faces = parent_mesh.faces[face_indices]
            faces = faces.ravel()
            faces = [renumber_dict[v] for v in faces]
            faces = np.array(faces)
            faces = faces.reshape((-1, 3))

            # Renumber vertices in full_path
            full_path_new = [renumber_dict[v] for v in full_path]
            face_norms = calc_face_normals(verts, faces)
            vert_norms = trimesh.geometry.mean_vertex_normals(verts.shape[0], faces, face_norms)

            mesh = trimesh.Trimesh(
                vertices=verts,
                faces=faces,
                face_normals=face_norms,
                vertex_normals=vert_norms,
                process=False,
            )

            return mesh, full_path_new

        def stitch_parent_and_child(parent_edge_vertices, junction_edge_vertices, parent_mesh, child_mesh):
            pass

        # Call the above functions to fuse the child and parent
        full_slice, slice_dist, u, slice_dist_approx = find_join_slice_along_child(
            parent_mesh,
            child_ac,
            num_steps_long_axis=10,
            num_steps_round_axis=6,
        )

        unique_NN, closest_NN = project_child_slice_onto_parent_mesh(parent_mesh, child_ac, slice_dist)

        full_path = find_path_between_projected_vertices(parent_mesh, unique_NN, closest_NN)
        plot_projected_vertices_and_NNs_3D(full_slice, closest_NN, parent_mesh.vertices, full_path)
        # plot_projected_vertices_and_NNs(self.full_slice_yz, closest_NN, self.mesh_verts_yz, full_path)

        surface, c_V, c_T = create_surface_between_child_slice_and_parent_mesh(parent_mesh, child_ac, closest_NN, u)
        child_mesh = stitch_child_and_junction(child_ac, surface, slice_dist_approx)
        # plot_surface_linking_axial_components(parent_mesh, child_ac, surface)

        # Delete the hole in the parent mesh
        new_mesh, full_path_new = remove_interior_vertices_from_parent(parent_mesh, full_path)

        # new_mesh = stitch_parent_and_child(parent_edge_vertices, junction_edge_vertices, parent_mesh, child_mesh)

        # Stitch together the two
        # For the smaller sequence, find the nearest neighbor of each vertex to points in the other sequence
        # Between these pairings, link points in the larger sequence to the first elmeent of each gap in the shorter sequence
        # Result is a list of edges which we will convert to faces

        pass

    def plot_meshes(self):

        trimesh.Scene([ac.mesh for ac in self.ac_list]).show()

    def merge_meshes(self):

        merged_meshes = trimesh.boolean.union([ac.mesh for ac in self.ac_list], engine="scad")
        bf = trimesh.repair.broken_faces(merged_meshes)
        self.merged_meshes = merged_meshes
