from splipy import Curve, BSplineBasis
from objects.parameters import NUM_SAMPLES_FOR_REPARAMETERIZATION, ORDER, NUM_INTERPOLATION_POINTS, EPSILON
from objects.utilities import open_uniform_knot_vector
import numpy as np


class Backbone:
    def __init__(self, controlpoints, reparameterize=True):

        self.controlpoints = controlpoints
        self.num_controlpoints = self.controlpoints.shape[0]

        # Construct B-Spline
        self.construct_B_spline()

        # Arc length parameterization
        if reparameterize is True:
            self.backbone = self.reparameterize()

    def construct_B_spline(self):
        """Construct the initial B-spline. This is formed by the relatively small number of control points that will give the curve its shape. An open uniform knot vector is used so that the endpoints are the first and last controlpoints. The resulting curved must be reparameterized to be arc length parameterized."""
        knot = open_uniform_knot_vector(self.num_controlpoints, ORDER)
        basis = BSplineBasis(order=ORDER, knots=knot, periodic=-1)
        self.backbone = Curve(basis=basis, controlpoints=self.controlpoints, rational=False)

    def reparameterize(self):
        """Create arc length parameterization of the backbone. This is works by sampling many evenly-spaced points along the original backbone and using these as the controlpoints of a new B-spline curve with a uniform knot-vector. This reparameterization is approximate. However, by choosing a large number of sample points, the curves become very close.

        See https://homepage.cs.uiowa.edu/~kearney/pubs/CurvesAndSurfacesArcLength.pdf for the idea."""

        #### Choose controlpoints that are evenly spaced

        # The arc length (that we want) to each control point
        target_arc_lengths = np.linspace(0, self.backbone.length(), NUM_INTERPOLATION_POINTS)

        # Sample many points along the backbone and choose the one that results in the arc length that is closest to our target arc length
        # This method seems coarse but is way faster than using a function optimizer (e.g. scipy.optimize.minimize), which is also an approximation.

        t = np.linspace(0, 1, NUM_SAMPLES_FOR_REPARAMETERIZATION)
        points = self.backbone(t)
        dists = np.linalg.norm(points[1:] - points[:-1], axis=1)
        cum_dists = np.cumsum(dists)  # Approximate distance by summing linear distances
        idx = np.searchsorted(cum_dists, target_arc_lengths, side="left")
        controlpoints = points[idx]

        #### Create new backbone that is reparameterized

        # Wrap first and last controlpoint so that new backbone goes through these endpoints
        NUM_EXTRA_CP = 2
        controlpoints_wrapped = np.zeros((NUM_INTERPOLATION_POINTS + NUM_EXTRA_CP, 3))
        controlpoints_wrapped[1:-1] = controlpoints
        controlpoints_wrapped[[0, -1]] = controlpoints[[0, -1]]  # Duplicate first and last cp

        # Construct new backbone
        knot = np.linspace(0, 1, NUM_INTERPOLATION_POINTS + ORDER + NUM_EXTRA_CP)  # uniform (not open uniform!)
        basis = BSplineBasis(order=ORDER, knots=knot, periodic=-1)
        backbone = Curve(basis=basis, controlpoints=controlpoints_wrapped, rational=False)
        backbone.reparam()  # Reparameterize between 0 and 1

        return backbone

    def dx(self, t):
        """First derivative (velocity) of b-spline backbone."""

        t = t.copy()  # Changing t was causing a bug

        # Handle array that may contain t == 0 or t == 1
        mask_t_0 = t == 0
        mask_t_1 = t == 1
        t[mask_t_0] = EPSILON
        t[mask_t_1] = 1 - EPSILON

        dx = self.backbone.derivative(t, 1)

        # Negative/positive values close to zero cause inconsistency when taking cross product
        dx = np.round(dx, 8)
        return dx

    # def dx(self, t):
    #     """Estimate first derivative."""

    #     return self.backbone.tangent(t)  # Use

    #     # # Handle array that may contain t == 0 or t == 1
    #     # mask_t_0 = t == 0
    #     # mask_t_1 = t == 1
    #     # t[mask_t_0] = EPSILON
    #     # t[mask_t_1] = 1 - EPSILON

    #     # # Numerator of first derivative limit
    #     # num = self.backbone(t + EPSILON) - self.backbone(t)

    #     # # Denominator of first derivative limit
    #     # den = np.repeat(EPSILON, len(t)).reshape(-1, 1)
    #     # den[mask_t_0] = 2 * EPSILON  # Epsilon was doubled in numerator, so double here as well
    #     # den[mask_t_1] = 2 * EPSILON  # Epsilon was doubled in numerator, so double here as well

    #     return np.round(num / den, 8)  # Round to simplifying catching colinear dx and ddx

    # def ddx(self, t):
    #     """Estimate second derivative."""

    #     # Handle array that may contain t == 0 or t == 1
    #     mask_t_0 = t == 0
    #     mask_t_1 = t == 1
    #     t[mask_t_0] = EPSILON
    #     t[mask_t_1] = 1 - EPSILON

    #     # Numerator of first derivative limit
    #     num = self.backbone(t + EPSILON) - 2 * self.backbone(t) + self.backbone(t - EPSILON)

    #     # Denominator of first derivative limit
    #     den = np.repeat(EPSILON, len(t)).reshape(-1, 1)
    #     den[mask_t_0] = 2 * EPSILON  # Epsilon was doubled in numerator, so double here as well
    #     den[mask_t_1] = 2 * EPSILON  # Epsilon was doubled in numerator, so double here as well

    #     return np.round(num / den ** 2, 8)  # Round to simplifying catching colinear dx and ddx

    def r(self, t):

        return self.backbone(t)

    def T(self, t):
        """Tangent vector is unit vector in same direction as velocity vector."""

        dx = self.dx(t)
        T = dx / np.linalg.norm(dx, axis=1, keepdims=True)
        return T

    def N(self, t):
        """Normal vector is unit vector that is perpendicular to tangent vector and to [0,0,1].

        I chose [0,0,1] arbitrarily, in any case, it will result in the binormal vector that is perpendicular to the tangent and is pointing "most upward" (has largest Z-component)."""

        UP_VECTOR = np.array([0, 0, 1])
        T = self.T(t)
        cross = np.cross(UP_VECTOR, T)

        # Normalize
        magnitude = np.linalg.norm(cross, axis=1, keepdims=True)
        assert np.all(
            ~np.isclose(magnitude, 0)
        ), "Normal vectors with 0 magnitude aren't valid. This may be because the tangent vector was colinear with [0,0,1]."
        N = cross / magnitude

        return N

    def B(self, t):
        """Binormal vector is unit vector that is perpendicular to tangent vector and closest to [0,0,1]."""

        T = self.T(t)
        N = self.N(t)
        B = np.cross(T, N)  # Already normalized
        return B

    def length(self):

        return self.backbone.length()
