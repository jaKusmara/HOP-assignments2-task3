def calcSquare(dim_series):
    return dim_series.apply(_compute_square)

def convertTo2D(dim_series):
    return dim_series.apply(lambda dims: _biggestDimensions(dims))

def _biggestDimensions(dims):
    if isinstance(dims, str):
        dims = dims.split('x')

    nums = [int(x) for x in dims if x.strip().isdigit()]

    return sorted(nums, reverse=True)[:2]

def _compute_square(dims):
    nums = [int(x) + 10 for x in dims]

    return nums[0] * nums[1]
