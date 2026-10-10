"""Literal, immutable fixtures for B2-021.

Box convention: float32 half-open pixel edges ``(x_min,y_min,x_max,y_max)``;
x increases right, y increases down, and arrays index ``[y,x]``. For an
``S x S`` grid, ``j=floor(cx*S/W)``, ``i=floor(cy*S/H)``, and the normalized
target is ``(cx*S/W-j, cy*S/H-i, w/W, h/H)``. Internal-boundary centers go to
the right/below cell; valid centers cannot equal the outer boundary. Graph
adjacency ``A[i,j]=1`` means receiver i reads sender j. All images are at most
8x8. Builders return fresh NumPy arrays, never mutable fixture storage.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import struct
from types import MappingProxyType
from typing import Mapping

import numpy as np

SEED = 20260901
BOX_CONVENTION = "half-open xyxy pixel edges; x right, y down; arrays index [y,x]"
GRID_ENCODING_CONVENTION = "j=floor(cx*S/W), i=floor(cy*S/H); target=(cx*S/W-j,cy*S/H-i,w/W,h/H); internal boundary goes right/below; largest area then lower-index tie"
GRAPH_CONVENTION = "A[i,j]=1 means node i receives from node j; self-loops included"

@dataclass(frozen=True)
class Component:
    dtype: str
    shape: tuple[int, ...]
    values: tuple[int | float, ...]

@dataclass(frozen=True)
class Example:
    example_id: str
    task: str
    feature_components: tuple[tuple[str, Component], ...]
    target_components: tuple[tuple[str, Component], ...]

def component(dtype: str, shape: tuple[int, ...], values: tuple[int | float, ...]) -> Component:
    return Component(dtype, shape, values)

def _array(value: Component) -> np.ndarray:
    return np.asarray(value.values, dtype=np.dtype(value.dtype)).reshape(value.shape).copy()

def canonical_structured_fingerprint(components: tuple[tuple[str, Component], ...]) -> str:
    """Hash ordered name/type/dtype/shape/contiguous-byte components."""
    return canonical_array_fingerprint(tuple((name, _array(value)) for name, value in components))

def canonical_array_fingerprint(components: tuple[tuple[str, np.ndarray], ...]) -> str:
    """Fingerprint actual ordered NumPy fields at a forward/loss seam."""
    h = hashlib.sha256()
    for name, value in components:
        if not isinstance(value, np.ndarray):
            raise TypeError("canonical fields must be NumPy arrays")
        arr = np.ascontiguousarray(value)
        for text in (name, "numpy.ndarray", arr.dtype.str):
            encoded = text.encode("utf-8")
            h.update(struct.pack(">I", len(encoded)))
            h.update(encoded)
        h.update(struct.pack(">I", arr.ndim))
        for size in arr.shape:
            h.update(struct.pack(">Q", size))
        payload = arr.tobytes(order="C")
        h.update(struct.pack(">Q", len(payload)))
        h.update(payload)
    return h.hexdigest()

_RECORDS = {
    'vit-train-00': Example('vit-train-00', 'vit', (('image', component('float32', (1, 4, 4), (0.20000000298023224, 0.0, 0.0, 0.0, 0.20000000298023224, 0.0, 0.0, 0.0, 0.20000000298023224, 0.0, 0.0, 0.0, 0.20000000298023224, 0.0, 0.0, 0.0))),), (('label', component('int64', (), (0,))),)),
    'vit-train-01': Example('vit-train-01', 'vit', (('image', component('float32', (1, 4, 4), (0.0, 0.30000001192092896, 0.0, 0.0, 0.0, 0.30000001192092896, 0.0, 0.0, 0.0, 0.30000001192092896, 0.0, 0.0, 0.0, 0.30000001192092896, 0.0, 0.0))),), (('label', component('int64', (), (0,))),)),
    'vit-train-02': Example('vit-train-02', 'vit', (('image', component('float32', (1, 4, 4), (0.800000011920929, 0.800000011920929, 0.800000011920929, 0.800000011920929, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('label', component('int64', (), (1,))),)),
    'vit-train-03': Example('vit-train-03', 'vit', (('image', component('float32', (1, 4, 4), (0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('label', component('int64', (), (1,))),)),
    'vit-heldout-00': Example('vit-heldout-00', 'vit', (('image', component('float32', (1, 4, 4), (0.25, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0))),), (('label', component('int64', (), (0,))),)),
    'vit-heldout-01': Example('vit-heldout-01', 'vit', (('image', component('float32', (1, 4, 4), (0.8999999761581421, 0.8999999761581421, 0.8999999761581421, 0.8999999761581421, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('label', component('int64', (), (1,))),)),
    'detection-train-00': Example('detection-train-00', 'detection', (('image', component('float32', (1, 8, 8), (1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('boxes', component('float32', (1, 4), (0.0, 0.0, 2.0, 2.0))), ('labels', component('int64', (1,), (0,))),)),
    'detection-train-01': Example('detection-train-01', 'detection', (('image', component('float32', (1, 8, 8), (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('boxes', component('float32', (1, 4), (2.0, 1.0, 4.0, 3.0))), ('labels', component('int64', (1,), (1,))),)),
    'detection-train-02': Example('detection-train-02', 'detection', (('image', component('float32', (1, 8, 8), (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('boxes', component('float32', (1, 4), (4.0, 4.0, 6.0, 6.0))), ('labels', component('int64', (1,), (0,))),)),
    'detection-train-03': Example('detection-train-03', 'detection', (('image', component('float32', (1, 8, 8), (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('boxes', component('float32', (1, 4), (6.0, 2.0, 8.0, 4.0))), ('labels', component('int64', (1,), (1,))),)),
    'detection-heldout-00': Example('detection-heldout-00', 'detection', (('image', component('float32', (1, 8, 8), (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('boxes', component('float32', (1, 4), (2.0, 4.0, 4.0, 6.0))), ('labels', component('int64', (1,), (0,))),)),
    'detection-heldout-01': Example('detection-heldout-01', 'detection', (('image', component('float32', (1, 8, 8), (0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('boxes', component('float32', (1, 4), (4.0, 0.0, 6.0, 2.0))), ('labels', component('int64', (1,), (1,))),)),
    'segmentation-train-00': Example('segmentation-train-00', 'segmentation', (('image', component('float32', (1, 8, 8), (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.05000000074505806, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('mask', component('int64', (8, 8), (0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))),)),
    'segmentation-train-01': Example('segmentation-train-01', 'segmentation', (('image', component('float32', (1, 8, 8), (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.05000000074505806, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('mask', component('int64', (8, 8), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))),)),
    'segmentation-train-02': Example('segmentation-train-02', 'segmentation', (('image', component('float32', (1, 8, 8), (0.05000000074505806, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('mask', component('int64', (8, 8), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))),)),
    'segmentation-train-03': Example('segmentation-train-03', 'segmentation', (('image', component('float32', (1, 8, 8), (0.0, 0.05000000074505806, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('mask', component('int64', (8, 8), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0))),)),
    'segmentation-heldout-00': Example('segmentation-heldout-00', 'segmentation', (('image', component('float32', (1, 8, 8), (0.0, 0.0, 0.0, 0.0, 0.0, 0.05000000074505806, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('mask', component('int64', (8, 8), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))),)),
    'segmentation-heldout-01': Example('segmentation-heldout-01', 'segmentation', (('image', component('float32', (1, 8, 8), (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.05000000074505806, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))),), (('mask', component('int64', (8, 8), (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))),)),
    'graph-train-00': Example('graph-train-00', 'graph', (('node_features', component('float32', (4, 3), (2.0, 0.0, 0.0, 2.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0))), ('adjacency', component('uint8', (4, 4), (1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1))),), (('label', component('int64', (), (0,))),)),
    'graph-train-01': Example('graph-train-01', 'graph', (('node_features', component('float32', (4, 3), (1.0, 0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 0.0, 0.0, 1.0, 0.0, 0.0))), ('adjacency', component('uint8', (4, 4), (1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1))),), (('label', component('int64', (), (0,))),)),
    'graph-train-02': Example('graph-train-02', 'graph', (('node_features', component('float32', (4, 3), (0.0, 2.0, 0.0, 0.0, 2.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0))), ('adjacency', component('uint8', (4, 4), (1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1))),), (('label', component('int64', (), (1,))),)),
    'graph-train-03': Example('graph-train-03', 'graph', (('node_features', component('float32', (4, 3), (0.0, 1.0, 0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 0.0, 0.0, 1.0, 0.0))), ('adjacency', component('uint8', (4, 4), (1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1))),), (('label', component('int64', (), (1,))),)),
    'graph-heldout-00': Example('graph-heldout-00', 'graph', (('node_features', component('float32', (4, 3), (2.0, 0.0, 0.10000000149011612, 1.0, 0.0, 0.0, 2.0, 0.0, 0.0, 1.0, 0.0, 0.0))), ('adjacency', component('uint8', (4, 4), (1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1))),), (('label', component('int64', (), (0,))),)),
    'graph-heldout-01': Example('graph-heldout-01', 'graph', (('node_features', component('float32', (4, 3), (0.0, 2.0, 0.10000000149011612, 0.0, 1.0, 0.0, 0.0, 2.0, 0.0, 0.0, 1.0, 0.0))), ('adjacency', component('uint8', (4, 4), (1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1))),), (('label', component('int64', (), (1,))),)),
}
RECORDS: Mapping[str, Example] = MappingProxyType(_RECORDS)

_TASK_SPLITS = {
    task: MappingProxyType({
        "train": tuple(eid for eid, row in RECORDS.items() if row.task == task and "-train-" in eid),
        "heldout": tuple(eid for eid, row in RECORDS.items() if row.task == task and "-heldout-" in eid),
    })
    for task in ("vit", "detection", "segmentation", "graph")
}
TASK_SPLITS = MappingProxyType(_TASK_SPLITS)
TRAIN_IDS = tuple(eid for task in TASK_SPLITS.values() for eid in task["train"])
HELDOUT_IDS = tuple(eid for task in TASK_SPLITS.values() for eid in task["heldout"])

FEATURE_FINGERPRINT_TO_ID = MappingProxyType({
    canonical_structured_fingerprint(row.feature_components): eid
    for eid, row in RECORDS.items()
})
EXAMPLE_ID_TO_TARGET_FINGERPRINT = MappingProxyType({
    eid: canonical_structured_fingerprint(row.target_components)
    for eid, row in RECORDS.items()
})

EXPECTED_LITERAL_HASHES = {'features': '4ce5df28d42d0d652f28f043aaadbe7263bb4fdc943b5c70a58e34eacf28531b', 'targets': '841bd5c2452656b4ed4876427c8e5c183fe2ac19dd678a8fbc90793d8d5c9ffe', 'splits': '02faa1f27e4dec6ad622914f4efb5c22baedc62e3a9b49c35e0fd5d564ea1fe6'}

def build_example(example_id: str) -> dict[str, object]:
    if example_id not in RECORDS:
        raise KeyError(f"unknown example_id: {example_id}")
    row = RECORDS[example_id]
    return {
        "example_id": example_id,
        "task": row.task,
        "features": {name: _array(value) for name, value in row.feature_components},
        "targets": {name: _array(value) for name, value in row.target_components},
    }

def build_task_batch(task: str, ids: tuple[str, ...]) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    if task not in TASK_SPLITS:
        raise KeyError(f"unknown task: {task}")
    if not isinstance(ids, tuple):
        raise TypeError("batch IDs must be a tuple")
    allowed = (TASK_SPLITS[task]["train"], TASK_SPLITS[task]["heldout"])
    if ids not in allowed:
        raise ValueError("IDs must equal one complete immutable split in stored order")
    rows = [build_example(eid) for eid in ids]
    if any(row["task"] != task for row in rows):
        raise ValueError("task/ID mismatch")
    feature_names = tuple(rows[0]["features"])
    target_names = tuple(rows[0]["targets"])
    features = {name: np.stack([row["features"][name] for row in rows]) for name in feature_names}
    targets = {name: np.stack([row["targets"][name] for row in rows]) for name in target_names}
    return features, targets

def validate_actual_batch(
    task: str,
    features: Mapping[str, np.ndarray],
    targets: Mapping[str, np.ndarray],
) -> tuple[str, tuple[str, ...]]:
    """Resolve actual rows by feature bytes and verify aligned target bytes."""
    if task not in TASK_SPLITS:
        raise KeyError(f"unknown task: {task}")
    if not features or not targets:
        raise ValueError("features and targets must be nonempty")
    feature_names = tuple(next(iter(RECORDS[eid].feature_components for eid in TASK_SPLITS[task]["train"])))
    target_names = tuple(next(iter(RECORDS[eid].target_components for eid in TASK_SPLITS[task]["train"])))
    feature_names = tuple(name for name, _ in feature_names)
    target_names = tuple(name for name, _ in target_names)
    if tuple(features) != feature_names or tuple(targets) != target_names:
        raise ValueError("feature/target fields or order mismatch")
    values = [*features.values(), *targets.values()]
    if any(not isinstance(value, np.ndarray) for value in values):
        raise TypeError("batch fields must be NumPy arrays")
    batch_sizes = {value.shape[0] for value in values if value.ndim >= 1}
    if len(batch_sizes) != 1:
        raise ValueError("batch dimensions disagree")
    batch_size = batch_sizes.pop()
    resolved: list[str] = []
    for index in range(batch_size):
        feature_fp = canonical_array_fingerprint(tuple((name, np.asarray(features[name][index])) for name in feature_names))
        eid = resolve_example_id(feature_fp)
        if RECORDS[eid].task != task:
            raise ValueError("actual feature belongs to another task")
        target_fp = canonical_array_fingerprint(tuple((name, np.asarray(targets[name][index])) for name in target_names))
        if target_fp != EXAMPLE_ID_TO_TARGET_FINGERPRINT[eid]:
            raise ValueError(f"aligned target mismatch for actual feature {eid}")
        resolved.append(eid)
    resolved_ids = tuple(resolved)
    for role in ("train", "heldout"):
        if resolved_ids == TASK_SPLITS[task][role]:
            return role, resolved_ids
    raise ValueError("actual batch is not one complete immutable split in stored order")

def build_train_batch(task: str) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Build a fresh deterministic batch in the immutable stored train order."""
    return build_task_batch(task, TASK_SPLITS[task]["train"])

def build_heldout_batch(task: str) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Build a fresh deterministic batch in the immutable held-out order."""
    return build_task_batch(task, TASK_SPLITS[task]["heldout"])

def resolve_example_id(feature_fingerprint: str) -> str:
    try:
        return FEATURE_FINGERPRINT_TO_ID[feature_fingerprint]
    except KeyError as exc:
        raise KeyError("unknown structured feature fingerprint") from exc

def validate_catalog(
    records: Mapping[str, Example] = RECORDS,
    splits: Mapping[str, Mapping[str, tuple[str, ...]]] = TASK_SPLITS,
    target_fingerprints: Mapping[str, str] = EXAMPLE_ID_TO_TARGET_FINGERPRINT,
) -> bool:
    seen: dict[str, str] = {}
    for eid, row in records.items():
        if eid != row.example_id:
            raise ValueError("record key/example_id mismatch")
        fingerprint = canonical_structured_fingerprint(row.feature_components)
        if fingerprint in seen:
            raise ValueError(f"duplicate feature fingerprint: {seen[fingerprint]} and {eid}")
        seen[fingerprint] = eid
        expected_target = canonical_structured_fingerprint(row.target_components)
        if target_fingerprints.get(eid) != expected_target:
            raise ValueError(f"aligned target mismatch for {eid}")
    if set(target_fingerprints) != set(records):
        raise ValueError("target fingerprint IDs do not equal record IDs")
    train: set[str] = set()
    heldout: set[str] = set()
    mentioned: list[str] = []
    for task, split in splits.items():
        for role in ("train", "heldout"):
            ids = split[role]
            for eid in ids:
                if eid not in records:
                    raise ValueError(f"unknown ID in split: {eid}")
                if records[eid].task != task:
                    raise ValueError(f"task split mismatch: {eid}")
                mentioned.append(eid)
            (train if role == "train" else heldout).update(ids)
    if train & heldout:
        raise ValueError(f"train/held-out split overlap: {sorted(train & heldout)}")
    if len(mentioned) != len(set(mentioned)):
        raise ValueError("ID repeated within split declarations")
    if set(mentioned) != set(records):
        raise ValueError("split declarations do not cover records exactly")
    return True

def literal_canonical_hashes() -> dict[str, str]:
    features = {eid: canonical_structured_fingerprint(row.feature_components) for eid, row in RECORDS.items()}
    targets = {eid: canonical_structured_fingerprint(row.target_components) for eid, row in RECORDS.items()}
    feature_hash = hashlib.sha256(json.dumps(features, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    target_hash = hashlib.sha256(json.dumps(targets, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    plain_splits = {task: {role: list(ids) for role, ids in split.items()} for task, split in TASK_SPLITS.items()}
    split_hash = hashlib.sha256(json.dumps(plain_splits, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"features": feature_hash, "targets": target_hash, "splits": split_hash}

def validate_literal_hashes() -> bool:
    actual = literal_canonical_hashes()
    if actual != EXPECTED_LITERAL_HASHES:
        raise ValueError(f"literal canonical hash drift: {actual}")
    return True

def exercise_validation_guards() -> tuple[str, ...]:
    caught: list[str] = []
    ids = tuple(RECORDS)
    duplicate = dict(RECORDS)
    duplicate[ids[-1]] = replace(duplicate[ids[-1]], feature_components=duplicate[ids[0]].feature_components)
    try:
        validate_catalog(duplicate, TASK_SPLITS, EXAMPLE_ID_TO_TARGET_FINGERPRINT)
    except ValueError as exc:
        if "duplicate feature" in str(exc):
            caught.append("duplicate-feature")
    bad_split = {task: {role: tuple(values) for role, values in split.items()} for task, split in TASK_SPLITS.items()}
    bad_split["vit"]["train"] += ("unknown-id",)
    try:
        validate_catalog(RECORDS, bad_split, EXAMPLE_ID_TO_TARGET_FINGERPRINT)
    except ValueError as exc:
        if "unknown ID" in str(exc):
            caught.append("unknown-id")
    bad_targets = dict(EXAMPLE_ID_TO_TARGET_FINGERPRINT)
    bad_targets[ids[0]] = "0" * 64
    try:
        validate_catalog(RECORDS, TASK_SPLITS, bad_targets)
    except ValueError as exc:
        if "target mismatch" in str(exc):
            caught.append("target-mismatch")
    overlap = {task: {role: tuple(values) for role, values in split.items()} for task, split in TASK_SPLITS.items()}
    overlap["vit"]["heldout"] += (overlap["vit"]["train"][0],)
    try:
        validate_catalog(RECORDS, overlap, EXAMPLE_ID_TO_TARGET_FINGERPRINT)
    except ValueError as exc:
        if "split overlap" in str(exc):
            caught.append("split-overlap")
    vit_train = TASK_SPLITS["vit"]["train"]
    for label, candidate in (
        ("batch-duplicate", (vit_train[0], vit_train[0], *vit_train[2:])),
        ("batch-reordered", tuple(reversed(vit_train))),
        ("batch-partial", vit_train[:-1]),
        ("batch-unknown", (*vit_train[:-1], "unknown-id")),
        ("batch-wrong-split", TASK_SPLITS["graph"]["train"]),
    ):
        try:
            build_task_batch("vit", candidate)
        except (KeyError, ValueError):
            caught.append(label)
    features, targets = build_train_batch("vit")
    if validate_actual_batch("vit", features, targets) != ("train", vit_train):
        raise RuntimeError("actual batch validation did not preserve stored order")
    corrupted = {name: value.copy() for name, value in targets.items()}
    corrupted[next(iter(corrupted))][0] = 1 - corrupted[next(iter(corrupted))][0]
    try:
        validate_actual_batch("vit", features, corrupted)
    except ValueError as exc:
        if "target mismatch" in str(exc):
            caught.append("actual-target-mismatch")
    return tuple(caught)

validate_catalog()
validate_literal_hashes()
