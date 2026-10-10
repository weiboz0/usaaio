#!/usr/bin/env python3
"""Regenerate and check B2-021 literal and seeded initial-state hashes.

This command instantiates the exact complete default-initialized p17-p20 models.
Each model resets ``torch.manual_seed(SEED)`` immediately before the constructor,
so a solution that uses the stated attribute/construction order has the same
state. Every parameter and persistent buffer in each ``state_dict`` is named,
shaped, typed, and hashed. The command never writes model state, trained
parameters, or evaluation values.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import struct
import sys

import torch

sys.dont_write_bytecode = True

SEED = 20260901
MODEL_CONSTRUCTION_ORDER = {'p17_vit': [['class_token', [1, 1, 8], 'float32'], ['positions', [1, 5, 8], 'float32'], ['patch.weight', [8, 4], 'float32'], ['patch.bias', [8], 'float32'], ['attention.in_proj_weight', [24, 8], 'float32'], ['attention.in_proj_bias', [24], 'float32'], ['attention.out_proj.weight', [8, 8], 'float32'], ['attention.out_proj.bias', [8], 'float32'], ['norm.weight', [8], 'float32'], ['norm.bias', [8], 'float32'], ['head.weight', [2, 8], 'float32'], ['head.bias', [2], 'float32']], 'p18_detector': [['stem.weight', [4, 1, 3, 3], 'float32'], ['stem.bias', [4], 'float32'], ['objectness.weight', [1, 4, 1, 1], 'float32'], ['objectness.bias', [1], 'float32'], ['class_head.weight', [2, 4, 1, 1], 'float32'], ['class_head.bias', [2], 'float32'], ['box.weight', [4, 4, 1, 1], 'float32'], ['box.bias', [4], 'float32']], 'p19_unet': [['encoder.weight', [4, 1, 3, 3], 'float32'], ['encoder.bias', [4], 'float32'], ['bottleneck.weight', [8, 4, 3, 3], 'float32'], ['bottleneck.bias', [8], 'float32'], ['decoder.weight', [8, 4, 2, 2], 'float32'], ['decoder.bias', [4], 'float32'], ['fuse.weight', [4, 8, 3, 3], 'float32'], ['fuse.bias', [4], 'float32'], ['head.weight', [2, 4, 1, 1], 'float32'], ['head.bias', [2], 'float32']], 'p20_graph': [['class_token', [1, 1, 8], 'float32'], ['project.weight', [8, 3], 'float32'], ['project.bias', [8], 'float32'], ['attention.in_proj_weight', [24, 8], 'float32'], ['attention.in_proj_bias', [24], 'float32'], ['attention.out_proj.weight', [8, 8], 'float32'], ['attention.out_proj.bias', [8], 'float32'], ['norm.weight', [8], 'float32'], ['norm.bias', [8], 'float32'], ['head.weight', [2, 8], 'float32'], ['head.bias', [2], 'float32']]}
EXPECTED_INITIAL_STATE_HASHES = {'p17_vit.class_token': 'cac288597320d981a482fab26183002e700833705a235a50f787e22cdb7ee693', 'p17_vit.positions': '1e436d6ce47aa430a95c5f2c4d463cb4871a9e74d6d042a13efbd195944d10c6', 'p17_vit.patch.weight': 'c16930a015295a6df531012aef1b3017b58b1e2c89067fb7d760e5059f43c5a9', 'p17_vit.patch.bias': 'b3712485c92c8b75e10a195e7079af54e30c40340ec63c3c4e9bb957dbcf185e', 'p17_vit.attention.in_proj_weight': '8f38d64c5479bf220eb144b81b9aa1c7563ed31d4aefa1061fe9b25acf65af33', 'p17_vit.attention.in_proj_bias': '9ff54e320a65d33a1bd12bc6a6ed406d7e1b0905c6087afac4bd485ed0dc7031', 'p17_vit.attention.out_proj.weight': 'e84a715ed8f97f9877313d68027085382eda7e352efbf27516a203b11238e0f3', 'p17_vit.attention.out_proj.bias': 'da0f254bb36f39c8d34019545e5cf65ba8247bb225b41bccd6365c573c33ced7', 'p17_vit.norm.weight': '01d467a479597650f547942cb55a8a8f59cad7c5733b18a02eb8366d936a5252', 'p17_vit.norm.bias': '0092aa8edde9dd958ad18e8b52644ec626061852ba3194cd3fd6d84487482edc', 'p17_vit.head.weight': '86eb886c3506f5388bd4f442f07eb113755179e8f588672debddfd579e2f119e', 'p17_vit.head.bias': '49663c5e2de4a5b968eb6a3abd760009bfa761ea77e6226372ce82c1490abaf2', 'p18_detector.stem.weight': '0a86b2b87c3708be8fe4db93c28cb96ae37dfd1fcd099c608639aba3510be273', 'p18_detector.stem.bias': 'ba6d968633fc3473926b48c24278a652d2a7c5ae1a4a0fd25902e696812c25a0', 'p18_detector.objectness.weight': '008de72df5741c688b4eaea02792275739e1d13d135171fbef422727a5c7d06b', 'p18_detector.objectness.bias': 'ff50492e2f687a00bccdf9c4f4fd8c909dc3a6e4e9b4d6b4972f967b6d6ea37c', 'p18_detector.class_head.weight': 'fa20abb611e45fcb9222469024db272641f3ee06378a208a698d49a83c539c17', 'p18_detector.class_head.bias': '1cf17712fdc483506c93b6bc3e786cc780818e0c3ecad337717188027bf64e8b', 'p18_detector.box.weight': 'c717e75964a98b31fac84c5f0c1d007aa28896374b64444a822d7279c30b7e53', 'p18_detector.box.bias': 'e8eaf410b114264cb24c5d9609015449783b11a63c688bb99638170efb1aca89', 'p19_unet.encoder.weight': '55b6c74ac629709f4628b01517e289ee11cf96cf77200183dcc592066d80da60', 'p19_unet.encoder.bias': '85f67d44ee7e8da2504bf58ba2cb4cc2dc086ebc620bd41f874eeb3b25d89071', 'p19_unet.bottleneck.weight': 'b9bc9768427235893d2bde9d366cff8cdfc2a0eb6be6b10179d63eb1bf42ea02', 'p19_unet.bottleneck.bias': 'abc6420eb746753f33ffde2ff6d27a4054c90e1e803b92c6adf6e8932d3a1728', 'p19_unet.decoder.weight': '4663aa53a3e67760a10e4da1b10daba34c3812cb89a6e3743723198d060eb658', 'p19_unet.decoder.bias': '4a8f839f1b07e44a85a59926f8b746ea257f827633767c21fd408fd6a118b4ce', 'p19_unet.fuse.weight': 'b6192f3ae6c1256409a91e9aa7875dceb04d99c3717ff430f7881a8f9172bc5f', 'p19_unet.fuse.bias': 'c4f7fc91d231a2958db309352d7b55b1f51fc3f5e8137f7d3ec457add5ca0ed8', 'p19_unet.head.weight': '7fb73587e789e1b2edfc5894dd04efe8fee34fdb6f2539890b9850043928d8d3', 'p19_unet.head.bias': '38c1d5db39f5ad5a6116c2b717a04c408e3f5012b4800f48575e0f5f761fc098', 'p20_graph.class_token': 'd9a04084739547c59d37275993b356f7e9dd4deb02e15de80c0f72856b91487e', 'p20_graph.project.weight': '2a64d10917515c5bbb55544196b45c306321a3b95f8cf17d70a78d534c9b4749', 'p20_graph.project.bias': '40ef68ba6519aa62119807c7d21a2b39eb81855c1587f138da89f19bc4657f59', 'p20_graph.attention.in_proj_weight': 'c3f7904d1a398b50ccf2f3be374660635ce8e4887cd35263f60603373d90bae1', 'p20_graph.attention.in_proj_bias': '764f507544e42fa913ce785737fde8af22b29538712cbed96e1f47ccaba3ce51', 'p20_graph.attention.out_proj.weight': '22737b6b214f678f2b68174cd321cc26a10c6da7582179a8372bc471a83a322b', 'p20_graph.attention.out_proj.bias': 'f8d3108c654ff87cd5a7b090b2cbfc232d390937ccbc6cd97d0fdc2ad1443a9e', 'p20_graph.norm.weight': '30ba4d61557b90e25d0ee0f231c620cca3e9c93f2ab901dec45747e661813268', 'p20_graph.norm.bias': 'ad0901afc13d9fd638e0bd2a027d16e7258c67f45d870a22652e5e15cc9eef3a', 'p20_graph.head.weight': 'fc078bd218c324f5d5d23f019d80caeec0b823ec32c1c0db310fbf6125209a7a', 'p20_graph.head.bias': '432a2168cf3875ca04dd99bb52dfdbb8026cbec7326e587864d8aed0fbbdcf61'}


class P17TinyVit(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.patch = torch.nn.Linear(4, 8, bias=True)
        self.class_token = torch.nn.Parameter(torch.zeros(1, 1, 8))
        self.positions = torch.nn.Parameter(torch.zeros(1, 5, 8))
        self.attention = torch.nn.MultiheadAttention(8, 1, dropout=0.0, batch_first=True)
        self.norm = torch.nn.LayerNorm(8, eps=1e-5)
        self.head = torch.nn.Linear(8, 2, bias=True)

    def forward(self, image):
        batch = image.shape[0]
        patches = image.reshape(batch, 1, 2, 2, 2, 2).permute(0, 2, 4, 1, 3, 5).contiguous().reshape(batch, 4, 4)
        tokens = torch.cat((self.class_token.expand(batch, -1, -1), self.patch(patches)), dim=1)
        positioned = tokens + self.positions
        attended, _ = self.attention(positioned, positioned, positioned, need_weights=False)
        encoded = self.norm(positioned + attended)
        return self.head(encoded[:, 0]), encoded[:, :1]

class P18TinyDetector(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.stem = torch.nn.Conv2d(1, 4, 3, stride=2, padding=1, bias=True)
        self.objectness = torch.nn.Conv2d(4, 1, 1, bias=True)
        self.class_head = torch.nn.Conv2d(4, 2, 1, bias=True)
        self.box = torch.nn.Conv2d(4, 4, 1, bias=True)

    def forward(self, image):
        hidden = torch.nn.functional.relu(self.stem(image))
        return self.objectness(hidden).squeeze(1), self.class_head(hidden), self.box(hidden).sigmoid()

class P19TinyUnet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = torch.nn.Conv2d(1, 4, 3, padding=1, bias=True)
        self.bottleneck = torch.nn.Conv2d(4, 8, 3, padding=1, bias=True)
        self.decoder = torch.nn.ConvTranspose2d(8, 4, 2, stride=2, bias=True)
        self.fuse = torch.nn.Conv2d(8, 4, 3, padding=1, bias=True)
        self.head = torch.nn.Conv2d(4, 2, 1, bias=True)

    def forward(self, image):
        skip = torch.nn.functional.relu(self.encoder(image))
        bottleneck = torch.nn.functional.relu(self.bottleneck(torch.nn.functional.max_pool2d(skip, 2)))
        decoded = torch.nn.functional.relu(self.decoder(bottleneck))
        concat = torch.cat((decoded, skip), dim=1)
        fused = self.fuse(concat)
        return self.head(fused), concat

class P20TinyGraph(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.project = torch.nn.Linear(3, 8, bias=True)
        self.class_token = torch.nn.Parameter(torch.zeros(1, 1, 8))
        self.attention = torch.nn.MultiheadAttention(8, 1, dropout=0.0, batch_first=True)
        self.norm = torch.nn.LayerNorm(8, eps=1e-5)
        self.head = torch.nn.Linear(8, 2, bias=True)

    def forward(self, node_features, adjacency):
        aggregate = torch.bmm(adjacency.float(), node_features) / adjacency.sum(-1, keepdim=True)
        projected = self.project(aggregate)
        tokens = torch.cat((self.class_token.expand(node_features.shape[0], -1, -1), projected), dim=1)
        attended, _ = self.attention(tokens, tokens, tokens, need_weights=False)
        encoded = self.norm(tokens + attended)
        return self.head(encoded[:, 0]), aggregate, tokens

def build_initial_models():
    models = {}
    for name, constructor in (
        ("p17_vit", P17TinyVit),
        ("p18_detector", P18TinyDetector),
        ("p19_unet", P19TinyUnet),
        ("p20_graph", P20TinyGraph),
    ):
        torch.manual_seed(SEED)
        models[name] = constructor().cpu()
    return models


def load_fixture():
    path = Path(__file__).resolve().parents[1] / "data/vision_fixture.py"
    spec = importlib.util.spec_from_file_location("b2021_vision_fixture", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load literal fixture")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def initial_state_hashes() -> dict[str, str]:
    hashes = {}
    actual_order = {}
    for model_name, model in build_initial_models().items():
        actual_order[model_name] = []
        for parameter_name, tensor in model.state_dict().items():
            name = f"{model_name}.{parameter_name}"
            array = tensor.detach().cpu().contiguous().numpy()
            actual_order[model_name].append([parameter_name, list(array.shape), str(array.dtype)])
            h = hashlib.sha256()
            h.update(name.encode("utf-8"))
            h.update(str(array.dtype).encode("utf-8"))
            h.update(struct.pack(">I", array.ndim))
            for size in array.shape:
                h.update(struct.pack(">Q", size))
            h.update(array.tobytes(order="C"))
            hashes[name] = h.hexdigest()
    if actual_order != MODEL_CONSTRUCTION_ORDER:
        raise RuntimeError(f"model parameter order/shape drift: {actual_order}")
    return hashes

def transient_forward_contracts() -> None:
    models = build_initial_models()
    with torch.no_grad():
        vit_logits, vit_class = models["p17_vit"](torch.zeros(2, 1, 4, 4))
        det_obj, det_cls, det_box = models["p18_detector"](torch.zeros(2, 1, 8, 8))
        seg_logits, seg_concat = models["p19_unet"](torch.zeros(2, 1, 8, 8))
        graph_logits, graph_aggregate, graph_tokens = models["p20_graph"](
            torch.zeros(2, 4, 3), torch.eye(4, dtype=torch.uint8).repeat(2, 1, 1))
    actual = (vit_logits.shape, vit_class.shape, det_obj.shape, det_cls.shape, det_box.shape,
              seg_logits.shape, seg_concat.shape, graph_logits.shape, graph_aggregate.shape, graph_tokens.shape)
    expected = ((2,2), (2,1,8), (2,4,4), (2,2,4,4), (2,4,4,4),
                (2,2,8,8), (2,8,8,8), (2,2), (2,4,3), (2,5,8))
    if tuple(tuple(shape) for shape in actual) != expected:
        raise RuntimeError(f"transient forward contract drift: {actual}")

def check() -> None:
    fixture = load_fixture()
    fixture.validate_catalog()
    if not fixture.validate_literal_hashes():
        raise RuntimeError("literal canonical hash validation returned false")
    actual = initial_state_hashes()
    if actual != EXPECTED_INITIAL_STATE_HASHES:
        raise RuntimeError(f"initial-state hash drift: {actual}")
    transient_forward_contracts()
    print(f"PASS: literal canonical hashes ({len(fixture.RECORDS)} immutable examples)")
    print(f"PASS: complete default-initialized model hashes ({len(actual)} tensors, seed={SEED}, CPU float32)")
    print("PASS: p17-p20 construction order, parameter names, shapes, dtypes, and bytes")
    print("PASS: p17-p20 transient forward paths and output shapes")
    print("PASS: no files, trained state, or evaluation values emitted")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    if args.check:
        check()

if __name__ == "__main__":
    main()
