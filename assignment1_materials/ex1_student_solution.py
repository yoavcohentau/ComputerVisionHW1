"""Projective Homography and Panorama Solution."""
import numpy as np

from typing import Tuple
from random import sample
from collections import namedtuple


from numpy.linalg import svd
from scipy.interpolate import griddata


PadStruct = namedtuple('PadStruct',
                       ['pad_up', 'pad_down', 'pad_right', 'pad_left'])


class Solution:
    """Implement Projective Homography and Panorama Solution."""
    def __init__(self):
        pass

    @staticmethod
    def compute_homography_naive(match_p_src: np.ndarray,
                                 match_p_dst: np.ndarray) -> np.ndarray:
        """Compute a Homography in the Naive approach, using SVD decomposition.

        Args:
            match_p_src: 2xN points from the source image.
            match_p_dst: 2xN points from the destination image.

        Returns:
            Homography from source to destination, 3x3 numpy array.
        """
        # return homography
        """INSERT YOUR CODE HERE"""
        A_list = []  # np.array([]).reshape(1, -1)
        for pixel_idx_src, pixel_idx_dst in zip(np.transpose(match_p_src), np.transpose(match_p_dst)):
            row1 = np.array([pixel_idx_src[0], pixel_idx_src[1], 1,
                             0, 0, 0,
                             -pixel_idx_dst[0]*pixel_idx_src[0], -pixel_idx_dst[0]*pixel_idx_src[1], -pixel_idx_dst[0]])
            A_list.append(row1)
            row2 = np.array([0, 0, 0,
                             pixel_idx_src[0], pixel_idx_src[1], 1,
                             -pixel_idx_dst[1]*pixel_idx_src[0], -pixel_idx_dst[1]*pixel_idx_src[1], -pixel_idx_dst[1]])
            A_list.append(row2)
        A = np.array(A_list)

        ATA = np.matmul(np.transpose(A), A)
        eig_val, eig_vec = np.linalg.eig(ATA)
        min_eig_idx = np.argmin(eig_val)
        min_eig_vec = eig_vec[:, min_eig_idx]
        transform_matrix = min_eig_vec.reshape(3, 3)
        return transform_matrix

    @staticmethod
    def compute_forward_homography_slow(
            homography: np.ndarray,
            src_image: np.ndarray,
            dst_image_shape: tuple = (1088, 1452, 3)) -> np.ndarray:
        """Compute a Forward-Homography in the Naive approach, using loops.

        Iterate over the rows and columns of the source image, and compute
        the corresponding point in the destination image using the
        projective homography. Place each pixel value from the source image
        to its corresponding location in the destination image.
        Don't forget to round the pixel locations computed using the
        homography.

        Args:
            homography: 3x3 Projective Homography matrix.
            src_image: HxWx3 source image.
            dst_image_shape: tuple of length 3 indicating the destination
            image height, width and color dimensions.

        Returns:
            The forward homography of the source image to its destination.
        """
        # return new_image
        """INSERT YOUR CODE HERE"""
        src_in_dst = np.zeros(shape=dst_image_shape, dtype=int)
        y_len, x_len = src_image.shape[0:2]
        for x in range(x_len):
            for y in range(y_len):
                src_vec = np.array([x, y, 1])
                dst_vec = np.matmul(homography, src_vec)
                dst_vec /= dst_vec[-1]
                dst_vec_round = np.round(np.array(dst_vec[0:2])).astype(int)
                if 0 <= dst_vec_round[0] <= dst_image_shape[1] and 0 <= dst_vec_round[1] <= dst_image_shape[0]:
                    src_in_dst[dst_vec_round[1], dst_vec_round[0], :] = src_image[y, x, :]
        return src_in_dst

    @staticmethod
    def compute_forward_homography_fast(
            homography: np.ndarray,
            src_image: np.ndarray,
            dst_image_shape: tuple = (1088, 1452, 3)) -> np.ndarray:
        """Compute a Forward-Homography in a fast approach, WITHOUT loops.

        (1) Create a meshgrid of columns and rows.
        (2) Generate a matrix of size 3x(H*W) which stores the pixel locations
        in homogeneous coordinates.
        (3) Transform the source homogeneous coordinates to the target
        homogeneous coordinates with a simple matrix multiplication and
        apply the normalization you've seen in class.
        (4) Convert the coordinates into integer values and clip them
        according to the destination image size.
        (5) Plant the pixels from the source image to the target image according
        to the coordinates you found.

        Args:
            homography: 3x3 Projective Homography matrix.
            src_image: HxWx3 source image.
            dst_image_shape: tuple of length 3 indicating the destination.
            image height, width and color dimensions.

        Returns:
            The forward homography of the source image to its destination.
        """
        # return new_image
        """INSERT YOUR CODE HERE"""

        # use meshgrid:
        y_len, x_len = src_image.shape[0:2]
        src_img_pixels = np.meshgrid(range(y_len), range(x_len))

        # generate matrix of size 3x(H*W):
        ones_layer = np.ones((1, y_len * x_len))
        index_array = np.concatenate((
            src_img_pixels[1].reshape(1, -1),
            src_img_pixels[0].reshape(1, -1),
            ones_layer
        ), axis=0)

        # apply homography transformation + normalization
        src_in_dst_idx = np.matmul(homography, index_array)
        src_in_dst_idx_y = np.divide(src_in_dst_idx[1], src_in_dst_idx[2])
        src_in_dst_idx_x = np.divide(src_in_dst_idx[0], src_in_dst_idx[2])
        src_in_dst_idx_y = np.round(np.array(src_in_dst_idx_y)).astype(int)
        src_in_dst_idx_x = np.round(np.array(src_in_dst_idx_x)).astype(int)

        # find valid-index in src image
        valid_idx = (0 <= src_in_dst_idx_x) & \
                    (src_in_dst_idx_x < dst_image_shape[1]) & \
                    (0 <= src_in_dst_idx_y) & \
                    (src_in_dst_idx_y < dst_image_shape[0])

        # prepare output image and plant the valid pixels
        src_in_dst = np.zeros(shape=dst_image_shape, dtype=int)
        src_in_dst[src_in_dst_idx_y[valid_idx], src_in_dst_idx_x[valid_idx], :] = src_image[
            src_img_pixels[0].reshape(1, -1).squeeze()[valid_idx],
            src_img_pixels[1].reshape(1, -1).squeeze()[valid_idx]]
        return src_in_dst

    @staticmethod
    def test_homography(homography: np.ndarray,
                        match_p_src: np.ndarray,
                        match_p_dst: np.ndarray,
                        max_err: float) -> Tuple[float, float]:
        """Calculate the quality of the projective transformation model.

        Args:
            homography: 3x3 Projective Homography matrix.
            match_p_src: 2xN points from the source image.
            match_p_dst: 2xN points from the destination image.
            max_err: A scalar that represents the maximum distance (in
            pixels) between the mapped src point to its corresponding dst
            point, in order to be considered as valid inlier.

        Returns:
            A tuple containing the following metrics to quantify the
            homography performance:
            fit_percent: The probability (between 0 and 1) validly mapped src
            points (inliers).
            dist_mse: Mean square error of the distances between validly
            mapped src points, to their corresponding dst points (only for
            inliers). In edge case where the number of inliers is zero,
            return dist_mse = 10 ** 9.
        """
        # return fit_percent, dist_mse
        """INSERT YOUR CODE HERE"""
        # generate matrix of size 3xlen(match_p):
        ones_layer = np.ones((1, len(match_p_src[0])))
        index_array = np.concatenate((
            match_p_src[0].reshape(1, -1),
            match_p_src[1].reshape(1, -1),
            ones_layer
        ), axis=0)

        # apply homography transformation + normalization
        src_in_dst_idx = np.matmul(homography, index_array)
        src_in_dst_idx_y = np.divide(src_in_dst_idx[1], src_in_dst_idx[2])
        src_in_dst_idx_x = np.divide(src_in_dst_idx[0], src_in_dst_idx[2])
        src_in_dst_idx_y = np.round(np.array(src_in_dst_idx_y)).astype(int)
        src_in_dst_idx_x = np.round(np.array(src_in_dst_idx_x)).astype(int)

        # find distances
        distances = np.sqrt((match_p_dst[0]-src_in_dst_idx_x)**2 + (match_p_dst[1]-src_in_dst_idx_y)**2)

        # find fit_precent
        inlier_idx = np.where(distances < max_err)[0]
        fit_precent = len(inlier_idx) / len(distances)

        # find dist_mse
        if len(inlier_idx) == 0:
            dist_mse = 10 ** 9
        else:
            dist_mse = np.mean(distances[inlier_idx]**2)

        return fit_precent, dist_mse

    @staticmethod
    def meet_the_model_points(homography: np.ndarray,
                              match_p_src: np.ndarray,
                              match_p_dst: np.ndarray,
                              max_err: float) -> Tuple[np.ndarray, np.ndarray]:
        """Return which matching points meet the homography.

        Loop through the matching points, and return the matching points from
        both images that are inliers for the given homography.

        Args:
            homography: 3x3 Projective Homography matrix.
            match_p_src: 2xN points from the source image.
            match_p_dst: 2xN points from the destination image.
            max_err: A scalar that represents the maximum distance (in
            pixels) between the mapped src point to its corresponding dst
            point, in order to be considered as valid inlier.
        Returns:
            A tuple containing two numpy nd-arrays, containing the matching
            points which meet the model (the homography). The first entry in
            the tuple is the matching points from the source image. That is a
            nd-array of size 2xD (D=the number of points which meet the model).
            The second entry is the matching points form the destination
            image (shape 2xD; D as above).
        """
        # return mp_src_meets_model, mp_dst_meets_model
        """INSERT YOUR CODE HERE"""
        # generate matrix of size 3xlen(match_p):
        ones_layer = np.ones((1, len(match_p_src[0])))
        index_array = np.concatenate((
            match_p_src[0].reshape(1, -1),
            match_p_src[1].reshape(1, -1),
            ones_layer
        ), axis=0)

        # apply homography transformation + normalization
        src_in_dst_idx = np.matmul(homography, index_array)
        src_in_dst_idx_y = np.divide(src_in_dst_idx[1], src_in_dst_idx[2])
        src_in_dst_idx_x = np.divide(src_in_dst_idx[0], src_in_dst_idx[2])
        src_in_dst_idx_y = np.round(np.array(src_in_dst_idx_y)).astype(int)
        src_in_dst_idx_x = np.round(np.array(src_in_dst_idx_x)).astype(int)

        # find distances
        distances = np.sqrt((match_p_dst[0]-src_in_dst_idx_x)**2 + (match_p_dst[1]-src_in_dst_idx_y)**2)

        # find inlier points
        inlier_idx = np.where(distances < max_err)[0]
        mp_src_meets_model = match_p_src[:, inlier_idx]
        mp_dst_meets_model = match_p_dst[:, inlier_idx]

        return mp_src_meets_model, mp_dst_meets_model

    def compute_homography(self,
                           match_p_src: np.ndarray,
                           match_p_dst: np.ndarray,
                           inliers_percent: float,
                           max_err: float) -> np.ndarray:
        """Compute homography coefficients using RANSAC to overcome outliers.

        Args:
            match_p_src: 2xN points from the source image.
            match_p_dst: 2xN points from the destination image.
            inliers_percent: The expected probability (between 0 and 1) of
            correct match points from the entire list of match points.
            max_err: A scalar that represents the maximum distance (in
            pixels) between the mapped src point to its corresponding dst
            point, in order to be considered as valid inlier.
        Returns:
            homography: Projective transformation matrix from src to dst.
        """
        # # use class notations:
        # w = inliers_percent
        # # t = max_err
        # # p = parameter determining the probability of the algorithm to
        # # succeed
        # p = 0.99
        # # the minimal probability of points which meets with the model
        # d = 0.5
        # # number of points sufficient to compute the model
        # n = 4
        # # number of RANSAC iterations (+1 to avoid the case where w=1)
        # k = int(np.ceil(np.log(1 - p) / np.log(1 - w ** n))) + 1
        # return homography
        """INSERT YOUR CODE HERE"""
        # use class notations:
        w = inliers_percent
        # threshold
        t = max_err
        # p = parameter determining the probability of the algorithm to succeed
        p = 0.99
        # the minimal probability of points which meets with the model
        d = 0.5
        # number of points sufficient to compute the model
        n = 4
        # number of RANSAC iterations (+1 to avoid the case where w=1)
        k = int(np.ceil(np.log(1 - p) / np.log(1 - w ** n))) + 1

        points_idx_vec = range(0, match_p_src.shape[1])
        best_homography = None
        best_fit_prob = 0  # should be d, but for continuous running - in any case return the best homography that was founded
        for iter in range(k):
            # points randomizing
            rand_points_idx = sample(points_idx_vec, 4)
            rand_points_src = match_p_src[:, rand_points_idx]
            rand_points_dst = match_p_dst[:, rand_points_idx]
            # compute homography
            homography = self.compute_homography_naive(rand_points_src, rand_points_dst)
            # find prob of points that meets the model
            fit_percent, _ = self.test_homography(homography, match_p_src, match_p_dst, t)
            if fit_percent >= best_fit_prob:
                best_homography = homography
                best_fit_prob = fit_percent
        return best_homography

    @staticmethod
    def compute_backward_mapping(
            backward_projective_homography: np.ndarray,
            src_image: np.ndarray,
            dst_image_shape: tuple = (1088, 1452, 3)) -> np.ndarray:
        """Compute backward mapping.

        (1) Create a mesh-grid of columns and rows of the destination image.
        (2) Create a set of homogenous coordinates for the destination image
        using the mesh-grid from (1).
        (3) Compute the corresponding coordinates in the source image using
        the backward projective homography.
        (4) Create the mesh-grid of source image coordinates.
        (5) For each color channel (RGB): Use scipy's interpolation.griddata
        with an appropriate configuration to compute the bi-cubic
        interpolation of the projected coordinates.

        Args:
            backward_projective_homography: 3x3 Projective Homography matrix.
            src_image: HxWx3 source image.
            dst_image_shape: tuple of length 3 indicating the destination shape.

        Returns:
            The source image backward warped to the destination coordinates.
        """

        # return backward_warp
        """INSERT YOUR CODE HERE"""

        # use meshgrid:
        y_len, x_len = dst_image_shape[0:2]
        dst_img_pixels = np.meshgrid(range(x_len), range(y_len))

        # generate matrix of size 3x(H*W):
        ones_layer = np.ones((1, y_len * x_len))
        index_array = np.concatenate((
            dst_img_pixels[0].reshape(1, -1),
            dst_img_pixels[1].reshape(1, -1),
            ones_layer
        ), axis=0)

        # apply backward homography transformation + normalization
        dst_in_src_idx = np.matmul(backward_projective_homography, index_array)
        dst_in_src_idx_y = np.divide(dst_in_src_idx[1], dst_in_src_idx[2])
        dst_in_src_idx_x = np.divide(dst_in_src_idx[0], dst_in_src_idx[2])
        # find valid-index in src image
        valid_idx = (0 <= np.round(dst_in_src_idx_x)) & \
                    (np.round(dst_in_src_idx_x) < src_image.shape[1]) & \
                    (0 <= np.round(dst_in_src_idx_y)) & \
                    (np.round(dst_in_src_idx_y) < src_image.shape[0])
        dst_in_src_points = np.concatenate((dst_in_src_idx_y[valid_idx].reshape(1, -1), dst_in_src_idx_x[valid_idx].reshape(1, -1)), axis=0).T

        # use meshgrid for src image:
        y_len, x_len = src_image.shape[0:2]
        src_img_pixels = np.meshgrid(range(x_len), range(y_len))

        # bi-linear interpolation
        src_img_y_pixels_flat = src_img_pixels[1].reshape(1, -1).squeeze()
        src_img_x_pixels_flat = src_img_pixels[0].reshape(1, -1).squeeze()
        src_img_points = np.concatenate((src_img_y_pixels_flat.reshape(1, -1), src_img_x_pixels_flat.reshape(1, -1)), axis=0).T
        r_src_image_flat = src_image[:, :, 0].reshape(1, -1).squeeze()
        g_src_image_flat = src_image[:, :, 1].reshape(1, -1).squeeze()
        b_src_image_flat = src_image[:, :, 2].reshape(1, -1).squeeze()

        r = griddata(src_img_points, r_src_image_flat, dst_in_src_points, fill_value=0, method='cubic')
        g = griddata(src_img_points, g_src_image_flat, dst_in_src_points, fill_value=0, method='cubic')
        b = griddata(src_img_points, b_src_image_flat, dst_in_src_points, fill_value=0, method='cubic')

        dst_image = np.zeros(dst_image_shape, dtype=int)
        dst_image[dst_img_pixels[1].reshape(1, -1).squeeze()[valid_idx], dst_img_pixels[0].reshape(1, -1).squeeze()[valid_idx], 0] = np.array(np.round(r), dtype=int)
        dst_image[dst_img_pixels[1].reshape(1, -1).squeeze()[valid_idx], dst_img_pixels[0].reshape(1, -1).squeeze()[valid_idx], 1] = np.array(np.round(g), dtype=int)
        dst_image[dst_img_pixels[1].reshape(1, -1).squeeze()[valid_idx], dst_img_pixels[0].reshape(1, -1).squeeze()[valid_idx], 2] = np.array(np.round(b), dtype=int)

        # import matplotlib.pyplot as plt
        # plt.figure()
        # plt.imshow(dst_image)
        # plt.title('Backward Panorama imperfect matches - RANSAC Homography')
        # plt.show()

        backward_warp = np.clip(dst_image, 0, 255).astype(np.uint8)
        return backward_warp

    @staticmethod
    def find_panorama_shape(src_image: np.ndarray,
                            dst_image: np.ndarray,
                            homography: np.ndarray
                            ) -> Tuple[int, int, PadStruct]:
        """Compute the panorama shape and the padding in each axes.

        Args:
            src_image: Source image expected to undergo projective
            transformation.
            dst_image: Destination image to which the source image is being
            mapped to.
            homography: 3x3 Projective Homography matrix.

        For each image we define a struct containing it's corners.
        For the source image we compute the projective transformation of the
        coordinates. If some of the transformed image corners yield negative
        indices - the resulting panorama should be padded with at least
        this absolute amount of pixels.
        The panorama's shape should be:
        dst shape + |the largest negative index in the transformed src index|.

        Returns:
            The panorama shape and a struct holding the padding in each axes (
            row, col).
            panorama_rows_num: The number of rows in the panorama of src to dst.
            panorama_cols_num: The number of columns in the panorama of src to
            dst.
            padStruct = a struct with the padding measures along each axes
            (row,col).
        """
        src_rows_num, src_cols_num, _ = src_image.shape
        dst_rows_num, dst_cols_num, _ = dst_image.shape
        src_edges = {}
        src_edges['upper left corner'] = np.array([1, 1, 1])
        src_edges['upper right corner'] = np.array([src_cols_num, 1, 1])
        src_edges['lower left corner'] = np.array([1, src_rows_num, 1])
        src_edges['lower right corner'] = \
            np.array([src_cols_num, src_rows_num, 1])
        transformed_edges = {}
        for corner_name, corner_location in src_edges.items():
            transformed_edges[corner_name] = homography @ corner_location
            transformed_edges[corner_name] /= transformed_edges[corner_name][-1]
        pad_up = pad_down = pad_right = pad_left = 0
        for corner_name, corner_location in transformed_edges.items():
            if corner_location[1] < 1:
                # pad up
                pad_up = max([pad_up, abs(corner_location[1])])
            if corner_location[0] > dst_cols_num:
                # pad right
                pad_right = max([pad_right,
                                 corner_location[0] - dst_cols_num])
            if corner_location[0] < 1:
                # pad left
                pad_left = max([pad_left, abs(corner_location[0])])
            if corner_location[1] > dst_rows_num:
                # pad down
                pad_down = max([pad_down,
                                corner_location[1] - dst_rows_num])
        panorama_cols_num = int(dst_cols_num + pad_right + pad_left)
        panorama_rows_num = int(dst_rows_num + pad_up + pad_down)
        pad_struct = PadStruct(pad_up=int(pad_up),
                               pad_down=int(pad_down),
                               pad_left=int(pad_left),
                               pad_right=int(pad_right))
        return panorama_rows_num, panorama_cols_num, pad_struct

    @staticmethod
    def add_translation_to_backward_homography(backward_homography: np.ndarray,
                                               pad_left: int,
                                               pad_up: int) -> np.ndarray:
        """Create a new homography which takes translation into account.

        Args:
            backward_homography: 3x3 Projective Homography matrix.
            pad_left: number of pixels that pad the destination image with
            zeros from left.
            pad_up: number of pixels that pad the destination image with
            zeros from the top.

        (1) Build the translation matrix from the pads.
        (2) Compose the backward homography and the translation matrix together.
        (3) Scale the homography as learnt in class.

        Returns:
            A new homography which includes the backward homography and the
            translation.
        """
        # return final_homography
        """INSERT YOUR CODE HERE"""
        translation_matrix = np.array([[1, 0, -pad_left],
                                       [0, 1, -pad_up],
                                       [0, 0, 1]])
        final_homography = np.matmul(backward_homography, translation_matrix)
        final_homography /= np.linalg.norm(final_homography)
        return final_homography

    def panorama(self,
                 src_image: np.ndarray,
                 dst_image: np.ndarray,
                 match_p_src: np.ndarray,
                 match_p_dst: np.ndarray,
                 inliers_percent: float,
                 max_err: float) -> np.ndarray:
        """Produces a panorama image from two images, and two lists of
        matching points, that deal with outliers using RANSAC.

        (1) Compute the forward homography and the panorama shape.
        (2) Compute the backward homography.
        (3) Add the appropriate translation to the homography so that the
        source image will plant in place.
        (4) Compute the backward warping with the appropriate translation.
        (5) Create the an empty panorama image and plant there the
        destination image.
        (6) place the backward warped image in the indices where the panorama
        image is zero.
        (7) Don't forget to clip the values of the image to [0, 255].


        Args:
            src_image: Source image expected to undergo projective
            transformation.
            dst_image: Destination image to which the source image is being
            mapped to.
            match_p_src: 2xN points from the source image.
            match_p_dst: 2xN points from the destination image.
            inliers_percent: The expected probability (between 0 and 1) of
            correct match points from the entire list of match points.
            max_err: A scalar that represents the maximum distance (in pixels)
            between the mapped src point to its corresponding dst point,
            in order to be considered as valid inlier.

        Returns:
            A panorama image.

        """
        # return np.clip(img_panorama, 0, 255).astype(np.uint8)
        """INSERT YOUR CODE HERE"""

        # (1) Compute the forward homography and the panorama shape
        homography = self.compute_homography(match_p_src, match_p_dst, inliers_percent, max_err)
        panorama_rows_num, panorama_cols_num, pad_struct = self.find_panorama_shape(src_image, dst_image, homography)
        panorama_shape = (panorama_rows_num, panorama_cols_num, 3)

        # (2) Compute the backward homography.
        backward_homography = np.linalg.inv(homography)

        # (3) Add the appropriate translation to the homography so that the source image will plant in place
        translated_backward_homography = self.add_translation_to_backward_homography(backward_homography, pad_struct.pad_left, pad_struct.pad_up)

        # (4) Compute the backward warping with the appropriate translation
        backward_warp = self.compute_backward_mapping(translated_backward_homography, src_image, panorama_shape)

        # (5) Create the empty panorama image and plant there the destination image
        panorama = np.zeros(panorama_shape, dtype=int)
        panorama[pad_struct.pad_up:pad_struct.pad_up+dst_image.shape[0], pad_struct.pad_left:pad_struct.pad_left+dst_image.shape[1], :] = dst_image

        # (6) place the backward warped image in the indices where the panorama image is zero
        mask_temp = np.full(panorama_shape[0:2], True, dtype=bool)
        mask_temp[pad_struct.pad_up:pad_struct.pad_up+dst_image.shape[0], pad_struct.pad_left:pad_struct.pad_left+dst_image.shape[1]] = False
        mask_3d = np.repeat(mask_temp[np.newaxis, :, :], 3, axis=0)
        mask_3d = np.transpose(mask_3d, (1, 2, 0))
        panorama[mask_3d] = backward_warp[mask_3d]

        # (7) Don't forget to clip the values of the image to [0, 255].
        panorama = np.clip(panorama, 0, 255).astype(np.uint8)

        # import matplotlib.pyplot as plt
        # plt.figure()
        # plt.imshow(panorama)
        # plt.title('Panorama Image')
        # plt.show()

        return panorama


