import pandas as pd

global packages_dimensions, input_file_boxes
package_types = {'package_type1': [800, 1200],
                 'package_type2': [800, 600]}  # dictionary of available package types with dimensions in cm


def if_box_fits_to_empty_package(box_dimensions, package_type):
    """
    This function check if a box of certain dimensions fits to package of package_type
    :param box_dimensions: [dimension_x,dimension_y]
    :param package_type: str 'package_type1', 'package_type2' etc corresponding to global variable package_types.keys()
    :return: True or False
    """
    package_dimensions = package_types[package_type]
    if (box_dimensions[0] > package_dimensions[0]) and (box_dimensions[0] > package_dimensions[1]):
        return False
    if (box_dimensions[1] > package_dimensions[1]) and (box_dimensions[1] > package_dimensions[0]):
        return False
    if (box_dimensions[0] > package_dimensions[0]) and (box_dimensions[0] < package_dimensions[1]):
        if box_dimensions[1] > package_dimensions[0]:
            return False
    if (box_dimensions[1] > package_dimensions[0]) and (box_dimensions[1] < package_dimensions[1]):
        if box_dimensions[0] > package_dimensions[0]:
            return False
    if (box_dimensions[0] > package_dimensions[1]) and (box_dimensions[0] < package_dimensions[0]):
        if box_dimensions[1] > package_dimensions[1]:
            return False
    if (box_dimensions[1] > package_dimensions[1]) and (box_dimensions[1] < package_dimensions[0]):
        if box_dimensions[0] > package_dimensions[1]:
            return False
    return True


def boxes_checked(boxes_df):
    """
    This function checks that boxes fit into packages of available package_types
    :param boxes_df: Pandas DataFrame with columns = ['box_index', 'dimension_x', 'dimension_y','package_index',
                'rotated', 'x_center' , 'y_center']
    :return: updated DataFrame of boxes
    """
    for index, box in boxes_df.iterrows():
        # check that box fits into dimensions of available package_types
        if_fits_to_packages = []
        for package_type in package_types.keys():
            if_fits_to_packages.append(if_box_fits_to_empty_package([box['dimension_x'],
                                                                     box['dimension_y']],
                                                                    package_type))
        if not any(if_fits_to_packages):
            print('box %.0fx%.0f does not fit to any of package types. Removing from shipping...' % (
                box['dimension_x'], box['dimension_y']))
            boxes_df.drop(boxes_df.index[index], inplace=True)
    return boxes_df


def get_boxes(filename):
    """
    This function reads in file with dimensions of boxes to be shipped,
    :param filename:
    :return: pandas DataFrame of boxes to be shipped with following columns:
    'box_index' - number of the box as read from the file
    'dimensions_x', 'dimension_y' - dimensions of box as read from file
    'package_index' - index of a package where box located, initialized with 0
    'rotated' - flag indicates if rotation happened, initialized with 'Not rotated'
    'x_center' , 'y_center' - x and y coordinates of box center
    """
    boxes_df = pd.read_excel(filename, names=['box_index', 'dimension_x', 'dimension_y'], header=0)
    boxes_df['package_index'] = 0
    boxes_df['rotated'] = 'Not rotated'
    boxes_df['x_center'] = 0.0
    boxes_df['y_center'] = 0.0
    boxes_df = boxes_checked(boxes_df)
    return boxes_df


def put_box_in_package(shipping_dict, box_index, package_index, coordinates):
    """
    assign random coordinates to box in package
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': pd.DataFrame(['package_index','package_type','dimension_x','dimension_y']),
    'boxes': pd.DataFrame(['box_index', 'dimension_x', 'dimension_y','package_index','rotated', 'x_center' , 'y_center']
    :param box_index: index of a box to be moved
    :param package_index: index of package where to put box
    :param coordinates: coordinates where to put box
    :return: updated shipping_dict
    """
    return shipping_dict


def pack_boxes_randomly(shipping_dict):
    """
    pack boxes in packages in random order,
    if next box doesn't fit into a package anymore,
    new packages is taken of a random type
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': pd.DataFrame(['package_index','package_type','dimension_x','dimension_y']),
    'boxes': pd.DataFrame(['box_index', 'dimension_x', 'dimension_y','package_index','rotated', 'x_center' , 'y_center']
    :return: updated shipping_dic
    """
    # n_boxes =
    return shipping_dict


def initialize_shipping(filename):
    """
    This function reads in file with dimensions of boxes to be shipped,
    randomly puts boxes in a number of packages
    fills in a dataframe with shipping info
    :param filename: name of the file with boxes for shipping
    :return: dictionary with initial random guess of shipping arrangement
    shipping_dict format:
    {'area': overall area occupied by all packages,
    'n_packages': number of packages,
     'packages': # pandas DataFrame with columns = ['package_index','package_type','dimension_x','dimension_y'],
     'boxes': # pandas DataFrame} with columns = ['box_index', 'dimension_x', 'dimension_y','package_index','rotated',
                'x_center' , 'y_center']
    """
    shipping_dict = dict(columns=['area', 'n_packages', 'packages', 'boxes'],
                         dtype=[float, int, pd.DataFrame, pd.DataFrame])
    # Add boxes for shipping:
    boxes_df = get_boxes(filename)
    shipping_dict['boxes'] = boxes_df
    # Pack boxes randomly
    shipping_dict = pack_boxes_randomly(shipping_dict)

    return shipping_dict
