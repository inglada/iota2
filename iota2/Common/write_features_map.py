"""
Functions used to write features maps
"""
import os
import logging
from typing import Optional, List, Dict, Union
import iota2.Common.FileUtils as fu
from logging import Logger
sensors_params_type = Dict[str, Union[str, List[str], int]]

LOGGER = logging.getLogger(__name__)


def write_features_by_chunk(tile: str,
                            working_directory: str,
                            output_path: str,
                            sar_optical_post_fusion: bool,
                            sensors_parameters: sensors_params_type,
                            ram: Optional[int] = 128,
                            mode: Optional[str] = "usually",
                            module_path: Optional[str] = None,
                            list_functions: Optional[List[str]] = None,
                            force_standard_labels: Optional[bool] = False,
                            number_of_chunks: Optional[int] = 50,
                            targeted_chunk: Optional[int] = None,
                            chunk_size_mode: Optional[str] = "split_number",
                            chunk_size_x: Optional[int] = None,
                            chunk_size_y: Optional[int] = None,
                            concat_mode: Optional[bool] = False,
                            logger: Optional[Logger] = LOGGER) -> None:
    """
    usage : compute from a stack of data -> gapFilling -> features computation
            -> sampleExtractions
    thanks to OTB's applications'

    IN:
        trainShape [string] : path to a vector shape containing points
        workingDirectory [string] : working directory path
        samples [string] : output sqlite file
        dataField [string] : data's field in trainShape
        tile [string] : actual tile to compute. (ex : T31TCJ)
        output_path [string] : output_path
        onlyMaskComm [bool] :  flag to stop the script after common Mask
                               computation
        onlySensorsMasks [bool] : compute only masks
        customFeatures [bool] : compute custom features
    OUT:
        sampleExtr [SampleExtraction OTB's object]:
    """
    # const
    # seed_position = -1
    from iota2.Common import GenerateFeatures as genFeatures
    from iota2.Common.customNumpyFeatures import compute_custom_features

    # tile = train_shape.split("/")[-1].split(".")[0].split("_")[0]

    working_directory_features = os.path.join(working_directory, tile)

    if not os.path.exists(working_directory_features):
        try:
            os.mkdir(working_directory_features)
        except OSError:
            logger.warning(f"{working_directory_features} allready exists")

    (all_features, feat_labels, dep_features) = genFeatures.generate_features(
        working_directory_features,
        tile,
        sar_optical_post_fusion,
        output_path,
        sensors_parameters,
        mode=mode,
        force_standard_labels=force_standard_labels)

    all_features.Execute()

    opath = os.path.join(output_path, "customF")
    if not os.path.exists(opath):
        os.mkdir(opath)
    output_name = os.path.join(opath, f"{tile}_chunk_{targeted_chunk}.tif")
    otbimage, feat_labels = compute_custom_features(
        tile=tile,
        output_path=output_path,
        sensors_parameters=sensors_parameters,
        module_path=module_path,
        list_functions=list_functions,
        otb_pipeline=all_features,
        feat_labels=feat_labels,
        path_wd=working_directory_features,
        targeted_chunk=targeted_chunk,
        number_of_chunks=number_of_chunks,
        chunk_size_x=chunk_size_x,
        chunk_size_y=chunk_size_y,
        chunk_size_mode=chunk_size_mode,
        concat_mode=concat_mode,
        output_name=output_name)

    return 0


def merge_features_maps(iota2_directory,
                        output_name=None,
                        res=10,
                        output_type="Float32",
                        compress=None):
    list_tile = fu.FileSearch_AND(os.path.join(iota2_directory, "customF"),
                                  True, ".tif")

    if output_name is None:
        feature_map = os.path.join(iota2_directory, "final",
                                   "features_map.tif")
    else:
        feature_map = os.path.join(iota2_directory, "final", output_name)
    if compress is None:
        compress_options = {"COMPRESS": "LZW", "BIGTIFF": "YES"}
    else:
        compress_options = compress
    fu.assembleTile_Merge(list_tile,
                          res,
                          feature_map,
                          output_type,
                          co=compress_options)
