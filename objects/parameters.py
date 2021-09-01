ORDER = 3  # quadratic B-spline
SLIDE_FACTOR = 0.3
SHRINK_FACTOR = 0.3
NUM_ENDPOINTS = 2  # Position 0.0 and 1.0 on the axial component's backbone
NUM_ENDPOINTS_SLOPE = 2  # Extra controlpoints that determine slope of spline at endpoint
NUM_CROSS_SECTION_SLOPE = (
    2  # Extra controlpoints that determine slope of spline at the cross sections closest to the endpoints
)
SAMPLING_DENSITY_U = 50  # How densely to sample along round axis of 'cylinder'
SAMPLING_DENSITY_V = 100  # How densely to sample along long axis of 'cylinder'
