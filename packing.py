from packing import *

import pandas as pd

global packages_dimensions, input_file_boxes
packages_dimension = [[800, 1200]]  # list of available dimensions of packages
input_file_boxes = 'task1 - ideal packaging.xlsx'


def initialize_shipping(filename):
    """
    This function reads in file with dimensions of boxes to be shipped,
    randomly puts boxes in a number of containers
    fills in a dataframe with shipping info
    :param filename: name of the file with boxes for shipping
    :return: dataframe with initial random guess of shipping arrangement
    """
    boxes_df = pd.read_excel(filename, header=0)
    shipping_dict = dict(columns=['area', 'n_containers', 'containers', 'boxes'],dtype = [float, int, list,pd.DataFrame])
    shipping_dict['boxes'] = boxes_df
    return shipping_dict
