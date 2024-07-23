```bash
pip install TensorImgUtils
```

-----

```python
from tensor_img_utils import TensorImgUtils

image = TensorImgUtils.convert_to_type(image, "BCHW")
image = TensorImgUtils.convert_to_type(image, "BHWC")
image = TensorImgUtils.convert_to_type(image, "HWC")

h_idx, w_idx = TensorImgUtils.infer_hw_axis(image)
height, width = TensorImgUtils.height_width(image)

smaller_axis = TensorImgUtils.smaller_axis(image)
larger_axis = TensorImgUtils.larger_axis(image)

tensor_type = identify_type(image)
>>> (["B", "H", "W"], "BHW")

larger_image = TensorImgUtils.most_pixels(image1, image2)
```

