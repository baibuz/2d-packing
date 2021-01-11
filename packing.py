import pandas as pd
import numpy as np

global packages_dimensions, input_file_boxes
package_types = {'package_type1': [800, 1200],
                 'package_type2': [800, 600]}  # dictionary of available package types with dimensions in cm


def if_box_fits_to_empty_package(box_dimension_x, box_dimension_y, package_type):
    """
    This function check if a box of certain dimensions fits to package of package_type
    :param box_dimension_y: height of box
    :param box_dimension_x: length of box
    :param package_type: str 'package_type1', 'package_type2' etc corresponding to global variable package_types.keys()
    :return: True or False
    """
    package_dimensions = package_types[package_type]
    if (box_dimension_x > package_dimensions[0]) and (box_dimension_x > package_dimensions[1]):
        return False
    if (box_dimension_y > package_dimensions[1]) and (box_dimension_y > package_dimensions[0]):
        return False
    if (box_dimension_x > package_dimensions[0]) and (box_dimension_x < package_dimensions[1]):
        if box_dimension_y > package_dimensions[0]:
            return False
    if (box_dimension_y > package_dimensions[0]) and (box_dimension_y < package_dimensions[1]):
        if box_dimension_x > package_dimensions[0]:
            return False
    if (box_dimension_x > package_dimensions[1]) and (box_dimension_x < package_dimensions[0]):
        if box_dimension_y > package_dimensions[1]:
            return False
    if (box_dimension_y > package_dimensions[1]) and (box_dimension_y < package_dimensions[0]):
        if box_dimension_x > package_dimensions[1]:
            return False
    return True


def boxes_checked(boxes_df):
    """
    This function checks that boxes fit into packages of available package_types,
    removes any packages that don't fit to neither of packages
    :param boxes_df: Pandas DataFrame with columns = ['box_index', 'dimension_x', 'dimension_y','package_id',
                'rotated', 'x_center' , 'y_center']
    :return: updated DataFrame of boxes
    """
    for index, box in boxes_df.iterrows():
        # check that box fits into dimensions of available package_types
        if_fits_to_packages = []
        for package_type in package_types.keys():
            if_fits_to_packages.append(if_box_fits_to_empty_package(box['dimension_x'],
                                                                    box['dimension_y'],
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
    'package_id' - id of a package where box located, initialized with 0
    'rotated' - flag indicates if rotation happened, initialized with 'Not rotated'
    'x_center' , 'y_center' - x and y coordinates of box center
    """
    boxes_df = pd.read_excel(filename, names=['box_index', 'dimension_x', 'dimension_y'], header=0)
    boxes_df['package_id'] = 0
    boxes_df['rotated'] = 'Not rotated'
    boxes_df['x_center'] = 0.0
    boxes_df['y_center'] = 0.0
    boxes_df = boxes_checked(boxes_df)
    return boxes_df


def pick_package_type(box):
    """
    This function picks a random package type if there are more than one available
    or returns the only available package type
    :param box: pd.DataFrame(['box_index', 'dimension_x', 'dimension_y','package_id','rotated', 'x_center' , 'y_center']
    :return: one of the keys from global dictionary package_types
    """
    if len(package_types) > 1:
        found = False
        available_types = list(package_types.keys())  # list of available package types
        while not found:
            ind = np.random.randint(0, len(available_types))  # random index of a package type
            package_type_to_fill = list(available_types)[ind]
            if if_box_fits_to_empty_package(box['dimension_x'],
                                            box['dimension_y'],
                                            package_type_to_fill):
                found = True
            else:
                available_types.remove(package_type_to_fill)
    else:
        package_type_to_fill = list(package_types.keys())[0]
        # sanity check:
        if not if_box_fits_to_empty_package(box['dimension_x'],
                                            box['dimension_y'],
                                            package_type_to_fill):
            print("DEBUG: Box doesn't fit into the only available package type. Exit ")
            return False
    return package_type_to_fill


def pick_package(shipping_dict):
    """
    randomly pick a package form the dictionary
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': pd.DataFrame(['package_id','package_type','dimension_x','dimension_y']),
    'boxes': pd.DataFrame(['box_index', 'dimension_x', 'dimension_y','package_id','rotated', 'x_center' , 'y_center']
    :return: package pd.DataFrame(['package_id','package_type','dimension_x','dimension_y'])
    """
    packages_df = shipping_dict['packages']
    if packages_df.empty:
        print("No packages to pick from shipping_dict, exit")
        return False
    ind = np.random.randint(0, len(package_types))
    package = packages_df.iloc[ind]
    return package


def pick_package_for_box(box, shipping_dict):
    """
    This function picks a random package from one of the packages in shipping_dict that satisfy condition
    that box fits to package dimension, returns id of a package
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': pd.DataFrame(['package_id','package_type','dimension_x','dimension_y']),
    'boxes': pd.DataFrame(['box_index', 'dimension_x', 'dimension_y','package_id','rotated', 'x_center' , 'y_center']
    :param box: pd.DataFrame(['box_index', 'dimension_x', 'dimension_y','package_id','rotated', 'x_center' , 'y_center']
    :return: package_id - id of a package where to put box
    """
    picked = False
    while not picked:
        package = pick_package(shipping_dict)
        if if_box_fits_to_empty_package(box['box_dimension_x'], box['box_dimension_y'], package['package_type']):
            picked = True
    return package['package_id']


def calculate_area_packages(packages_df):
    """
    calculate sum of packages area of packages
    :param packages_df: pd.DataFrame(['package_id','package_type','dimension_x','dimension_y']
    :return: area: sum of packages area
    """
    area = sum([package['dimension_x'] * package['dimension_y'] for index, package in packages_df.iterrows()])
    return area


def add_package(shipping_dict, package_type):
    """
    add package of package_type to shipping_dict
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': pd.DataFrame(['package_id','package_type','dimension_x','dimension_y']),
    'boxes': pd.DataFrame(['box_index', 'dimension_x', 'dimension_y','package_id','rotated', 'x_center' , 'y_center']
    :param package_type: one of the keys from global dictionary package_types
    :return: updated shipping_dict
    """
    packages_df = shipping_dict['packages']
    if packages_df.empty:
        package_id = 1
    else:
        package_id = max([package['package_id'] for index, package in packages_df.iterrows()]) + 1
    new_package = pd.DataFrame({'package_id': [package_id],
                                'package_type': [package_type],
                                'dimension_x': [package_types[package_type][0]],
                                'dimension_y': [package_types[package_type][1]]})
    packages_df = packages_df.append(new_package, ignore_index=True)
    shipping_dict['packages'] = packages_df
    shipping_dict['n_packages'] = shipping_dict['n_packages'] + 1
    shipping_dict['area'] = calculate_area_packages(shipping_dict['packages'])
    return shipping_dict


def put_box_in_package(shipping_dict, box_index, package_id,):
    """
    assign random coordinates to box in package
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': pd.DataFrame(['package_id','package_type','dimension_x','dimension_y']),
    'boxes': pd.DataFrame(['box_index', 'dimension_x', 'dimension_y','package_id','rotated', 'x_center' , 'y_center']
    :param box_index: index of a box to be moved
    :param package_id: id of package where to put box
    :return: updated shipping_dict
    """

    return shipping_dict


def pack_boxes_randomly(shipping_dict):
    """
    pack boxes in packages in random order,
    if next box doesn't fit into a package anymore,
    new packages of a random type is taken
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': pd.DataFrame(['package_id','package_type','dimension_x','dimension_y']),
    'boxes': pd.DataFrame(['box_index', 'dimension_x', 'dimension_y','package_id','rotated', 'x_center' , 'y_center']
    :return: updated shipping_dic
    """
    boxes_df = shipping_dict['boxes']
    packages_df = shipping_dict['packages']

    random_box_index_list = np.random.permutation(len(boxes_df))
    for box_index in random_box_index_list:
        box = boxes_df.iloc[box_index]
        # pick package where to put box
        if packages_df.empty:
            # if shipping_dic doesn't have any packages yet, pick a type of a package randomly, but so box would fit
            package_type_to_fill = pick_package_type(box)
            # add new package to shipping
            shipping_dict = add_package(shipping_dict, package_type_to_fill)
            # put box to package into a lower left corner
            package_id = 1
        else:
            # pick a random package out of existing, but so box would fit
            package_id = pick_package_for_box(shipping_dict, box)
        # put box of box_index
        shipping_dict = put_box_in_package(shipping_dict, box_index, package_id)

    return shipping_dict


def initialize_shipping(filename):
    """
    This function reads in file with dimensions of boxes to be shipped,
    randomly puts boxes in a number of packages,
    fills in a dataframe with shipping info
    :param filename: name of the file with boxes for shipping
    :return: dictionary with initial random guess of shipping arrangement
    shipping_dict format:
    {'area': overall area occupied by all packages,
    'n_packages': number of packages,
     'packages': # pandas DataFrame with columns = ['package_id','package_type','dimension_x','dimension_y'],
     'boxes': # pandas DataFrame} with columns = ['box_index', 'dimension_x', 'dimension_y','package_id','rotated',
                'x_center' , 'y_center']
    """
    shipping_dict = dict(columns=['area', 'n_packages', 'packages', 'boxes'],
                         dtype=[float, int, pd.DataFrame, pd.DataFrame])
    shipping_dict['area'] = 0
    shipping_dict['n_packages'] = 0
    shipping_dict['packages'] = pd.DataFrame(columns=['package_id', 'package_type', 'dimension_x', 'dimension_y'])
    # Add boxes for shipping:
    boxes_df = get_boxes(filename)
    shipping_dict['boxes'] = boxes_df
    # Pack boxes randomly
    shipping_dict = pack_boxes_randomly(shipping_dict)

    return shipping_dict
