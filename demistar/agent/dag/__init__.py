"""Support for computing functions that depend on each other in a pipeline, this can be used to route observations/actions in an agent.

TODO give details & examples.
"""

from .graph import ComputeGraph
from .from_ import From

__all__ = ["ComputeGraph", "From"]
