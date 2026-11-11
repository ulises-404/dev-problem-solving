import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import onnx
import onnxruntime as ort
import numpy as np
from onnx import TensorProto, helper

from quantize_onnx import quantize_model


def create_model(path: Path) -> None:
    input_info = helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 2])
    output_info = helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 1])
    weights = helper.make_tensor("weights", TensorProto.FLOAT, [2, 1], [1.0, -1.0])
    graph = helper.make_graph(
        [helper.make_node("MatMul", ["input", "weights"], ["output"])],
        "synthetic",
        [input_info],
        [output_info],
        [weights],
    )
    model = helper.make_model(
        graph,
        opset_imports=[helper.make_opsetid("", 11)],
        ir_version=6,
    )
    onnx.save(model, path)


class QuantizeOnnxTests(unittest.TestCase):
    def test_quantizes_and_publishes_valid_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / "input.onnx"
            destination = folder / "output.onnx"
            create_model(source)

            result = quantize_model(source, destination)

            onnx.checker.check_model(str(destination))
            self.assertEqual(result["weight_type"], "QUInt8")
            self.assertEqual(result["bytes"], destination.stat().st_size)
            quantized = onnx.load(destination)
            self.assertTrue(
                any(node.op_type == "MatMulInteger" for node in quantized.graph.node)
            )
            self.assertTrue(
                any(
                    tensor.data_type == TensorProto.UINT8
                    for tensor in quantized.graph.initializer
                )
            )
            session = ort.InferenceSession(
                str(destination), providers=["CPUExecutionProvider"]
            )
            output = session.run(
                None, {"input": np.array([[2.0, 1.0]], dtype=np.float32)}
            )[0]
            self.assertEqual(output.shape, (1, 1))
            self.assertAlmostEqual(float(output[0, 0]), 1.0, delta=0.1)

    def test_failed_quantization_preserves_previous_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source = folder / "input.onnx"
            destination = folder / "output.onnx"
            create_model(source)
            create_model(destination)
            original = destination.read_bytes()

            with patch(
                "onnxruntime.quantization.quantize_dynamic",
                side_effect=RuntimeError("synthetic conversion failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "synthetic conversion"):
                    quantize_model(source, destination)

            self.assertEqual(destination.read_bytes(), original)
            onnx.checker.check_model(str(destination))
            self.assertEqual(list(folder.glob(".output.onnx.*.onnx")), [])


if __name__ == "__main__":
    unittest.main()
