from torch import Tensor
from typing import Tuple, Callable


class TensorImgUtils:
    """
    Utility functions for working with image tensors when the shapes/types aren't static or well defined.

    Note:
        For some inferences, it's assumed that the batch dimension will be a singleton.

        `squeeze(dim)` and `unsqueeze(dim)` remove/add singleton dimensions to tensors. Adding a singleton
        dimension expands the tensor's shape by introducing an additional axis with a size of 1.

        Since a mask tensor's channel dimension is a singleton dimension, it's indistinguishable from a batch 
        dimension with size 1. So, there's no way to tell whether a `[1, H, W]` tensor is [B, H, W] or [A, H, W] 
        (where `A` represents an alpha channel).

    Known Types:
        - HW: Height x Width
        - HWC: Height x Width x Channel
        - HWA: Height x Width x Alpha
        - AHW: Alpha x Height x Width
        - BHWC: Batch x Height x Width x Channel
        - BCHW: Batch x Channel x Height x Width
        - BHWA: Batch x Height x Width x Alpha
        - BAHW: Batch x Alpha x Height x Width
        - BHW: Batch x Height x Width

    """

    @staticmethod
    def from_to(from_type: list[str], to_type: list[str]) -> Callable[[Tensor], Tensor]:
        """Return a function that converts a tensor from one type to another. Args can be lists of strings or just strings (e.g., ["C", "H", "W"] or just "CHW")."""
        if isinstance(from_type, list):
            from_type = "".join(from_type)
        if isinstance(to_type, list):
            to_type = "".join(to_type)

        permute_arg = [from_type.index(c) for c in to_type]

        def convert(tensor: Tensor) -> Tensor:
            return tensor.permute(permute_arg)

        return convert

    @staticmethod
    def convert_to_type(tensor: Tensor, to_type: str) -> Tensor:
        """Convert a tensor to a specific type."""
        from_type = TensorImgUtils.identify_type(tensor)[0]
        if from_type == list(to_type):
            return tensor

        if len(from_type) == 4 and len(to_type) == 3:
            # If converting from a batched tensor to a non-batched tensor, squeeze the batch dimension
            tensor = tensor.squeeze(0)
            from_type = from_type[1:]
        if len(from_type) == 3 and len(to_type) == 4:
            # If converting from a non-batched tensor to a batched tensor, unsqueeze the batch dimension
            tensor = tensor.unsqueeze(0)
            from_type = ["B"] + from_type

        return TensorImgUtils.from_to(from_type, list(to_type))(tensor)

    @staticmethod
    def infer_hw_axis(image: Tensor) -> Tuple[int, int]:
        """Infer the height and width axes of the image tensor

        Returns:
            Tuple[int, int]: The indices of the height and width axes
        """
        tensor_type = TensorImgUtils.identify_type(image)[1]
        if tensor_type in ["HWRGB", "HWRGBA", "HWA"]:
            return (0, 1)
        elif tensor_type in ["RGBHW", "RGBAHW", "AHW"]:
            return (1, 2)
        elif tensor_type == "BHWRGB":
            return (1, 2)
        elif tensor_type == "BRGBHW":
            return (2, 3)

    @staticmethod
    def height_width(image: Tensor) -> Tuple[int, int]:
        """Return the height and width of the image tensor.

        Returns:
            Tuple[int, int]: The height and width of the image tensor
        """
        h_axis, w_axis = TensorImgUtils.infer_hw_axis(image)
        return image.size(h_axis), image.size(w_axis)

    @staticmethod
    def smaller_axis(image: Tensor) -> int:
        """Return the axis with the smaller size.

        Returns:
            int: The index of the axis with the smaller size
        """
        h, w = TensorImgUtils.height_width(image)
        h_axis, w_axis = TensorImgUtils.infer_hw_axis(image)
        return h_axis if h < w else w_axis

    @staticmethod
    def larger_axis(image: Tensor) -> int:
        """Return the axis with the larger size.

        Returns:
            int: The index of the axis with the larger size
        """
        h, w = TensorImgUtils.height_width(image)
        h_axis, w_axis = TensorImgUtils.infer_hw_axis(image)
        return h_axis if h > w else w_axis

    @staticmethod
    def identify_type(tensor: Tensor) -> Tuple[list[str], str]:
        """Identify the type of image tensor. Doesn't currently check for BHW. Returns one of the following:"""
        dim_n = tensor.dim()
        if dim_n == 2:
            return (["H", "W"], "HW")
        elif dim_n == 3:  # HWA, AHW, HWC, or CHW
            if tensor.size(2) == 3:
                return (["H", "W", "C"], "HWRGB")
            if tensor.size(2) == 4:
                return (["H", "W", "C"], "HWRGBA")
            if tensor.size(0) == 3:
                return (["C", "H", "W"], "RGBHW")
            if tensor.size(0) == 4:
                return (["C", "H", "W"], "RGBAHW")
            if tensor.size(2) == 1 and tensor.size(0) >= 64: # Opinionated
                return (["H", "W", "C"], "HWA")
            if tensor.size(0) == 1:
                return (["C", "H", "W"], "AHW") # Opinionated
            if tensor.size(0) >= 2 and tensor.size(1) >= 64:
                return (["B", "H", "W"], "BHW")  # Assume [B, H, W] with multiple in batch (e.g., latent/mask batch)
        elif dim_n == 4:
            if tensor.size(3) >= 3:  # BHWRGB or BHWRGBA
                if tensor.size(3) == 3:
                    return (["B", "H", "W", "C"], "BHWRGB")
                if tensor.size(3) == 4:
                    return (["B", "H", "W", "C"], "BHWRGBA")

            if tensor.size(1) >= 3:
                if tensor.size(1) == 3:
                    return (["B", "C", "H", "W"], "BRGBHW")
                if tensor.size(1) == 4:
                    return (["B", "C", "H", "W"], "BRGBAHW")
            
            if tensor.size(0) == 1 and tensor.size(3) == 1: 
                return (["B", "H", "W", "C"], "BHWA") # (Opinionated) Assume a mask with [B, H, W, 1 Channel]
            if tensor.size(1) == 1:
                return (["B", "C", "H", "W"], "BAHW")

        else:
            raise ValueError(
                f"{dim_n} dimensions is not a valid number of dimensions for an image tensor."
            )

        raise ValueError(
            f"Could not determine shape of Tensor with {dim_n} dimensions and {tensor.shape} shape."
        )

    @staticmethod
    def test_squeeze_batch(tensor: Tensor, strict=False) -> Tensor:
        """Check if the tensor has a batch dimension squeeze it if it does."""
        if tensor.dim() == 4:
            if tensor.size(0) == 1 or not strict:
                return tensor.squeeze(0)
            else:
                raise ValueError(
                    f"This is not a single image. It's a batch of {tensor.size(0)} images."
                )
        else:
            return tensor

    @staticmethod
    def test_unsqueeze_batch(tensor: Tensor) -> Tensor:
        """Add a batch dimension at index 0 if the tensor doesn't already have one."""
        tensor_type = TensorImgUtils.identify_type(tensor)[0]
        if tensor_type[0] == "B":
            return tensor
        return tensor.unsqueeze(0)

    @staticmethod
    def most_pixels(img_tensors: list[Tensor]) -> Tensor:
        """Return the tensor with the most pixels."""
        sizes = [
            TensorImgUtils.height_width(img)[0] * TensorImgUtils.height_width(img)[1]
            for img in img_tensors
        ]
        return img_tensors[sizes.index(max(sizes))]