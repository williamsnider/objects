### Parameters used in generating objects

# AxialComponent construction
SAMPLING_DENSITY_U = 100  # Number of samples along round axis of 'cylinder' axial component
SAMPLING_DENSITY_V = 100  # Number of samples along long axis of 'cylinder' axial component
SLIDE_FACTOR = 0.3  # Impacts surface slope near endpoints
SHRINK_FACTOR = 0.3  # Impacts surface slope at cross sections adjacent to endpoint
ORDER = 3  # quadratic B-spline

# Shape construction
HARMONIC_POWER = 3  # 2-> G1 curvature fairing, 3-> G2 curvature fairing, etc
FAIRING_DISTANCE = 0.1  # How far (mm) from a junction should vertices in a union mesh be faired

# Interface construction
CUBE_SIDE_LENGTH = 25  # mm
POST_RADIUS = 5
POST_HEIGHT = 15
POST_SECTIONS = 10  # Strangely, 8 causes the interface to be non-watertight
FINGERTIP_SLOT_SIDE_LENGTH = 5
PEG_SIDE_LENGTH = 10  # mm
PEG_DEPTH = 12  # mm
