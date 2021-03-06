from objects.axial_component import AxialComponent
from objects.cross_section import CrossSection
from objects.shape import Shape
from objects.backbone import Backbone
from objects.components import cp_round, backbone_flat
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

c = np.cos
s = np.sin
base_cp = np.array(
    [
        [c(0 / 6 * 2 * np.pi), s(0 / 6 * 2 * np.pi)],
        [c(1 / 6 * 2 * np.pi), s(1 / 6 * 2 * np.pi)],
        [c(2 / 6 * 2 * np.pi), s(2 / 6 * 2 * np.pi)],
        [c(3 / 6 * 2 * np.pi), s(3 / 6 * 2 * np.pi)],
        [c(4 / 6 * 2 * np.pi), s(4 / 6 * 2 * np.pi)],
        [0.1, 0.1],
    ]
)

# Plot tangent vectors
def plot_tangent_vectors():
    cp = np.array([[0, 0, 0], [0, 10, 0], [0, 20, 0], [0, 30, 0], [10, 30, 0], [20, 30, 0], [30, 30, 0]])
    backbone = Backbone(cp, reparameterize=True)
    t = np.linspace(0, 1, 3)
    v = np.linspace(0, 1, 51)
    r = backbone.r(v)
    T = backbone.T(t)
    N = backbone.N(t)
    B = backbone.B(t)

    # Plot
    fig = plt.figure()
    ax = plt.axes(projection="3d")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    maxcp = cp.max()
    ax.set_xlim([-maxcp, maxcp])
    ax.set_ylim([-maxcp, maxcp])
    ax.set_zlim([-maxcp, maxcp])
    ax.view_init(elev=-90, azim=90)
    ax.plot3D(r[:, 0], r[:, 1], r[:, 2], "k.")

    # Plot lines
    for i, vec in enumerate([T, N, B]):
        color = ["red", "green", "blue"][i]
        for j, t_val in enumerate(t):

            p0 = backbone.r(t_val)
            p1 = p0 + vec[j, :] * 0.1
            line = np.stack([p0, p1], axis=0)
            x, y, z = line.T
            ax.plot(x, y, z, "-", color=color)
    plt.show()


# Plot tangent vectors
def plot_tangent_vectors_digit_segment():
    t = np.linspace(0, 1, 5)
    cp = np.stack(
        [
            1 - np.cos(t),
            np.sin(t),
            np.zeros(5),
        ]
    ).T  # Transpose so that cp are along rows
    backbone = Backbone(cp, reparameterize=False)

    t = np.linspace(0, 1, 5)
    v = np.linspace(0, 1, 51)
    r = backbone.r(v)
    T = backbone.T(t)
    N = backbone.N(t)
    B = backbone.B(t)

    # Plot
    fig = plt.figure()
    ax = plt.axes(projection="3d")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    maxcp = cp.max()
    ax.set_xlim([-maxcp, maxcp])
    ax.set_ylim([-maxcp, maxcp])
    ax.set_zlim([-maxcp, maxcp])
    ax.view_init(elev=-90, azim=90)
    ax.plot3D(r[:, 0], r[:, 1], r[:, 2], "k.")

    # Plot lines
    for i, vec in enumerate([T, N, B]):
        color = ["red", "green", "blue"][i]
        for j, t_val in enumerate(t):

            p0 = backbone.r(t_val)[0]
            p1 = p0 + vec[j, :] * 0.1
            line = np.stack([p0, p1], axis=0)
            x, y, z = line.T
            ax.plot(x, y, z, "-", color=color)
    plt.show()


def plot_controlpoints():
    cp = np.array([[0, 0, 0], [0, 10, 0], [0, 20, 0], [0, 30, 0], [10, 30, 0], [20, 30, 0], [30, 30, 0]])
    backbone = Backbone(cp, reparameterize=True)
    cs0 = CrossSection(base_cp * 10, position=0.3, tilt=np.pi / 4)
    cs1 = CrossSection(base_cp * 10, position=0.7, rotation=np.pi)
    ac = AxialComponent(backbone, cross_sections=[cs0, cs1])

    # Controlpoints
    ac.get_controlpoints()
    cp = ac.controlpoints
    x = cp[:, :, 0].ravel()
    y = cp[:, :, 1].ravel()
    z = cp[:, :, 2].ravel()

    # Backbone
    v = np.linspace(0, 1, 51)
    r = ac.r(v)

    # Plot
    fig = plt.figure()
    ax = plt.axes(projection="3d")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    maxcp = cp.max()
    ax.set_xlim([-maxcp, maxcp])
    ax.set_ylim([-maxcp, maxcp])
    ax.set_zlim([-maxcp, maxcp])
    ax.view_init(elev=-90, azim=90)
    ax.plot3D(r[:, 0], r[:, 1], r[:, 2], "k.")
    ax.plot3D(x, y, z, "g-")
    plt.show()


def plot_surface():
    cp = np.array([[0, 0, 0], [0, 10, 0], [0, 20, 0], [0, 30, 0], [10, 30, 0], [20, 30, 0], [30, 30, 0]])
    backbone = Backbone(cp, reparameterize=True)
    cs0 = CrossSection(base_cp * 10, position=0.3, tilt=np.pi / 4)
    cs1 = CrossSection(base_cp * 10, position=0.7, rotation=np.pi)
    ac = AxialComponent(backbone, cross_sections=[cs0, cs1])
    ac.get_controlpoints()
    ac.make_surface()

    # Backbone
    v = np.linspace(0, 1, 51)
    r = ac.r(v)

    # Surface
    uu = np.linspace(0, 1, 20)
    grid = ac.surface(uu, uu)
    sx, sy, sz = grid.reshape(-1, ac.surface.dimension).T
    cx, cy, cz = ac.surface.controlpoints.T

    # Plot
    fig = plt.figure()
    ax = plt.axes(projection="3d")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    maxcp = cp.max()
    ax.set_xlim([-maxcp, maxcp])
    ax.set_ylim([-maxcp, maxcp])
    ax.set_zlim([-maxcp, maxcp])
    ax.view_init(elev=-90, azim=90)
    # ax.plot3D(r[:, 0], r[:, 1], r[:, 2], "k.")
    # ax.plot3D(cx.ravel(), cy.ravel(), cz.ravel(), "g.")
    ax.plot3D(sx, sy, sz, "r-")

    plt.show()

    ac.mesh.show()


def plot_align_axial_components():
    cp = np.array([[0, 0, 0], [0, 10, 0], [0, 20, 0], [0, 30, 0], [10, 30, 0], [20, 30, 0], [30, 30, 0]])
    backbone = Backbone(cp, reparameterize=True)
    cs0 = CrossSection(base_cp * 10, position=0.3, tilt=np.pi / 4)
    cs1 = CrossSection(base_cp * 10, position=0.7, rotation=np.pi)
    ac1 = AxialComponent(backbone, cross_sections=[cs0, cs1])  # XXX: Maybe need to do backbone.copy()
    ac2 = AxialComponent(
        backbone,
        cross_sections=[cs0, cs1],
        parent_axial_component=ac1,
        position_along_parent=0.75,
        position_along_self=0.25,
        euler_angles=np.array([np.pi / 3, np.pi / 3, np.pi / 3]),
    )
    ac3 = AxialComponent(
        backbone,
        cross_sections=[cs0, cs1],
        parent_axial_component=ac2,
        position_along_parent=0.75,
        position_along_self=0.25,
    )

    # Plot backbones
    fig = plt.figure()
    ax = plt.axes(projection="3d")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    maxcp = cp.max()
    ax.set_xlim([-maxcp, maxcp])
    ax.set_ylim([-maxcp, maxcp])
    ax.set_zlim([-maxcp, maxcp])
    ax.view_init(elev=-90, azim=90)

    # Plot lines
    for ac in [ac1, ac2, ac3]:

        t = np.linspace(0, 1, 3)
        v = np.linspace(0, 1, 51)
        r = ac.r(v)
        T = ac.T(t)
        N = ac.N(t)
        B = ac.B(t)

        if ac == ac1:
            ax.plot3D(r[:, 0], r[:, 1], r[:, 2], "k.")

            # Plot controlpoints
            cp = ac.controlpoints
            x = cp[:, :, 0].ravel()
            y = cp[:, :, 1].ravel()
            z = cp[:, :, 2].ravel()
            ax.plot3D(x, y, z, "k-")

        if ac == ac2:
            ax.plot3D(r[:, 0], r[:, 1], r[:, 2], "y.")

            # Plot controlpoints
            cp = ac.controlpoints
            x = cp[:, :, 0].ravel()
            y = cp[:, :, 1].ravel()
            z = cp[:, :, 2].ravel()
            ax.plot3D(x, y, z, "y-")

        if ac == ac3:
            ax.plot3D(r[:, 0], r[:, 1], r[:, 2], "c.")

            # Plot controlpoints
            cp = ac.controlpoints
            x = cp[:, :, 0].ravel()
            y = cp[:, :, 1].ravel()
            z = cp[:, :, 2].ravel()
            ax.plot3D(x, y, z, "c-")

        for i, v in enumerate([T, N, B]):
            color = ["red", "green", "blue"][i]
            for j, t_val in enumerate(t):

                p0 = ac.r(t_val)
                p1 = p0 + v[j, :] * 0.1
                line = np.stack([p0, p1], axis=0)
                x, y, z = line.T
                ax.plot3D(x[0], y[0], z[0], "-", color=color)

    plt.show()


def plot_euler_angles():

    cp = np.array([[0, 0, 0], [0, 10, 0], [0, 20, 0], [0, 30, 0], [10, 30, 0], [20, 30, 0], [30, 30, 0]])
    backbone = Backbone(cp, reparameterize=True)
    cs0 = CrossSection(base_cp * 10, position=0.3, tilt=np.pi / 4)
    cs1 = CrossSection(base_cp * 10, position=0.7, rotation=np.pi)
    ac1 = AxialComponent(backbone, cross_sections=[cs0, cs1])
    ac2 = AxialComponent(
        backbone,
        cross_sections=[cs0, cs1],
        parent_axial_component=ac1,
        position_along_parent=0.75,
        position_along_self=0.25,
        euler_angles=np.array([0, 0, 0]),
    )
    ac3 = AxialComponent(
        backbone,
        cross_sections=[cs0, cs1],
        parent_axial_component=ac2,
        position_along_parent=0.75,
        position_along_self=0.25,
        euler_angles=np.array([0, 0, np.pi]),
    )

    # Plot backbones
    fig = plt.figure()
    ax = plt.axes(projection="3d")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    maxcp = cp.max()
    ax.set_xlim([-maxcp, maxcp])
    ax.set_ylim([-maxcp, maxcp])
    ax.set_zlim([-maxcp, maxcp])
    ax.view_init(elev=-90, azim=90)

    # Plot lines
    for ac in [ac1, ac2, ac3]:

        t = np.linspace(0, 1, 3)
        v = np.linspace(0, 1, 51)
        r = ac.r(v)
        T = ac.T(t)
        N = ac.N(t)
        B = ac.B(t)

        if ac == ac1:
            ax.plot3D(r[:, 0], r[:, 1], r[:, 2], "k.")

            # Plot controlpoints
            cp = ac.controlpoints
            x = cp[:, :, 0].ravel()
            y = cp[:, :, 1].ravel()
            z = cp[:, :, 2].ravel()
            ax.plot3D(x, y, z, "k-")

        if ac == ac2:
            ax.plot3D(r[:, 0], r[:, 1], r[:, 2], "y.")

            # Plot controlpoints
            cp = ac.controlpoints
            x = cp[:, :, 0].ravel()
            y = cp[:, :, 1].ravel()
            z = cp[:, :, 2].ravel()
            ax.plot3D(x, y, z, "y-")

        if ac == ac3:
            ax.plot3D(r[:, 0], r[:, 1], r[:, 2], "c.")

            # Plot controlpoints
            cp = ac.controlpoints
            x = cp[:, :, 0].ravel()
            y = cp[:, :, 1].ravel()
            z = cp[:, :, 2].ravel()
            ax.plot3D(x, y, z, "c-")

        for i, v in enumerate([T, N, B]):
            color = ["red", "green", "blue"][i]
            for j, t_val in enumerate(t):

                p0 = ac.r(t_val)
                p1 = p0 + v[j, :] * 0.1
                line = np.stack([p0, p1], axis=0)
                x, y, z = line.T
                ax.plot3D(x[0], y[0], z[0], "-", color=color)

    plt.show()


def plot_meshes_as_shape():
    cp = np.array([[0, 0, 0], [0, 10, 0], [0, 20, 0], [0, 30, 0], [10, 30, 0], [20, 30, 0], [30, 30, 0]])
    backbone = Backbone(cp, reparameterize=True)
    cs0 = CrossSection(base_cp * 10, position=0.3, tilt=np.pi / 4)
    cs1 = CrossSection(base_cp * 10, position=0.7, rotation=np.pi)
    ac1 = AxialComponent(backbone, cross_sections=[cs0, cs1])
    ac2 = AxialComponent(
        backbone,
        cross_sections=[cs0, cs1],
        parent_axial_component=ac1,
        position_along_parent=0.75,
        position_along_self=0.25,
        euler_angles=np.array([0, np.pi / 3, np.pi / 3]),
    )
    ac3 = AxialComponent(
        backbone,
        cross_sections=[cs0, cs1],
        parent_axial_component=ac2,
        position_along_parent=0.75,
        position_along_self=0.25,
        euler_angles=np.array([0, 0, np.pi]),
    )
    s = Shape([ac1, ac2, ac3])
    s.mesh.show()


def plot_axial_component_roundover():
    # Varying cross section relative sizes
    size = np.array([0.5, 1, 2])  # quadratic increase (flare)
    backbone = backbone_flat
    cp = cp_round
    rotation = 0
    cs_list = [
        CrossSection(cp * size[0], 0.1, rotation=rotation),
        CrossSection(cp * size[1], 0.5, rotation=rotation),
        CrossSection(cp * size[2], 0.9, rotation=rotation),
    ]
    ac = AxialComponent(backbone=backbone, cross_sections=cs_list)
    s = Shape([ac])
    s.mesh.show()


def show_fused_interface():
    # Steps to constructions shapes, rendering png and forming stl
    from objects.components import (
        backbone_flat,
        cp_round,
    )
    from objects.cross_section import CrossSection
    from objects.axial_component import AxialComponent
    from objects.shape import Shape
    import numpy as np

    # Dictionary linking names and arrays (helps with constructing description of each shape)
    d = {
        "b_flat": (backbone_flat),
        "cs_round": (cp_round),
    }
    ##########################
    ### Shape Construction ###
    ##########################

    # Varying backbones
    for b_name in ["b_flat"]:
        cs_name = "cs_round"
        backbone = d[b_name]
        cp = d[cs_name]
        rotation = 0
        cs_list = [CrossSection(cp, i, rotation=rotation) for i in np.linspace(0.1, 0.9, 5)]
        ac = AxialComponent(backbone=backbone, cross_sections=cs_list)
        s = Shape([ac])
        s.description = "{0}-{1}".format(b_name, cs_name)
        s.cs_name = [cs_name]
        s.sd_name = None

        s.create_interface()
        s.fuse_mesh_to_interface()
        s.mesh_with_interface.show()


if __name__ == "__main__":
    # plot_tangent_vectors()
    # plot_tangent_vectors_digit_segment()
    # plot_controlpoints()
    # plot_surface()
    # plot_align_axial_components()
    # plot_euler_angles()
    # plot_meshes_as_shape()
    # plot_axial_component_roundover()
    show_fused_interface()
