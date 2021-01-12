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
    :return: updated list of boxes
    """
    updated_boxes = []
    for box in boxes_df:
        # check that box fits into dimensions of available package_types
        if_fits_to_packages = []  # array of boolean
        for package_type in package_types.keys():
            if_fits_to_packages.append(if_box_fits_to_empty_package(box['dimension_x'],
                                                                    box['dimension_y'],
                                                                    package_type))
        if not any(if_fits_to_packages):
            print('box %.0fx%.0f does not fit to any of package types. Removing from shipping...' % (
                box['dimension_x'], box['dimension_y']))
            continue
        updated_boxes.append(box)
    return updated_boxes


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
    boxes_df = []
    for index, box in pd.read_excel(filename, names=['box_index', 'dimension_x', 'dimension_y'], header=0).iterrows():
        box = box.to_dict()
        box['package_id'] = 0
        box['rotated'] = 'Not rotated'
        box['x_center'] = 0.0
        box['y_center'] = 0.0
        boxes_df.append(box)

    boxes_df = boxes_checked(boxes_df)
    return boxes_df


def pick_package_type(box):
    """
    This function picks a random package type if there are more than one available
    or returns the only available package type
    :param box: {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}
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
        if not if_box_fits_to_empty_package(box['dimension_x'][0],
                                            box['dimension_y'][0],
                                            package_type_to_fill):
            print("DEBUG: Box doesn't fit into the only available package type. Exit ")
            return False
    return package_type_to_fill


def pick_package(shipping_dict):
    """
    randomly pick a package form the dictionary
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :return: package dictionary {'package_id':,'package_type':,'dimension_x':,'dimension_y':}
    """
    packages_df = shipping_dict['packages']
    if len(packages_df) == 0:
        print("No packages to pick from shipping_dict, exit")
        return False
    ind = np.random.randint(0, len(packages_df))
    package = packages_df[ind]
    return package


def if_box_fits_to_package(box_index, package_id, shipping_dict):
    """
    return true if box fits to package from shipping_dict
    :param box_index: index of box in shipping_dict
    :param package_id: index of package in shipping_dict
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :return: True or False
    """
    '''
    boxes_df = shipping_dict['boxes']
    box_to_fit = (boxes_df.loc[boxes_df['box_index'] == box_index]).to_dict('list')
    box_dimension_y = box_to_fit['dimension_y']
    packages_df = shipping_dict['packages'].to_list()
    package = (packages_df.loc[packages_df['package_id'] == package_id]).to_dict('list')

    # list boxes that are already in package_id
    boxes_in_package = [box for box in boxes_df]
    '''
    return True


def pick_package_for_box(box, shipping_dict):
    """
    This function picks a random package from one of the packages in shipping_dict that satisfy condition that box
    fits to package dimension, returns id of a package :param shipping_dict: dictionary with a shipping info in a
    format: {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]]
    :param box: dictionary with keys  {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':,
    'rotated':,'x_center': , 'y_center':}
    :return: package_id - id of a package where to put box
    """
    picked = False
    while not picked:
        package = pick_package(shipping_dict)
        if if_box_fits_to_package(box['box_index'], package['package_id'], shipping_dict):
            picked = True
    return package['package_id']


def calculate_area_packages(packages_df):
    """
    calculate sum of packages area of packages
    :param packages_df: list of package dictionaries in format:
    [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}]
    :return: area: sum of packages area
    """
    area = sum([package['dimension_x'] * package['dimension_y'] for package in packages_df])
    return area


def add_package(shipping_dict, package_type):
    """
    add package of package_type to shipping_dict
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]}
    :param package_type: one of the keys from global dictionary package_types
    :return: updated shipping_dict
    """
    packages_df = shipping_dict['packages']
    if len(packages_df) == 0:
        package_id = 1
    else:
        package_id = max([package['package_id'] for package in packages_df]) + 1
    new_package = {'package_id': package_id,
                   'package_type': package_type,
                   'dimension_x': package_types[package_type][0],
                   'dimension_y': package_types[package_type][1]}
    packages_df.append(new_package)
    shipping_dict['packages'] = packages_df
    shipping_dict['n_packages'] = shipping_dict['n_packages'] + 1
    shipping_dict['area'] = calculate_area_packages(shipping_dict['packages'])
    return shipping_dict


def if_intersect(box_1, box_2):
    """
    return True if box_1 intersect with box_2 in x direction
    :param box_1: {['box_index', 'dimension_x', 'dimension_y','package_id','rotated', 'x_center' , 'y_center']}
    :param box_2: {['box_index', 'dimension_x', 'dimension_y','package_id','rotated', 'x_center' , 'y_center']}
    :return: True of False
    """
    right_edge_box_1 = box_1['x_center'] + box_1['dimension_x'] / 2.0
    left_edge_box_1 = box_1['x_center'] - box_1['dimension_x'] / 2.0
    right_edge_box_2 = box_2['x_center'] + box_2['dimension_x'] / 2.0
    left_edge_box_2 = box_2['x_center'] - box_2['dimension_x'] / 2.0
    # if (left_edge_box_1 < right_edge_box_2 and left_edge_box_1 >= left_edge_box_2) or (right_edge_box_1 >
    # left_edge_box_2 and right_edge_box_1 <= right_edge_box_2) or (left_edge_box_1 >= left_edge_box_2 and
    # right_edge_box_1 <= right_edge_box_2) or (left_edge_box_1 <= left_edge_box_2 and right_edge_box_1 >=
    # right_edge_box_2):
    if (right_edge_box_2 > left_edge_box_1 >= left_edge_box_2) or \
            (left_edge_box_2 < right_edge_box_1 <= right_edge_box_2) or \
            (left_edge_box_1 >= left_edge_box_2 and right_edge_box_1 <= right_edge_box_2) or \
            (left_edge_box_1 <= left_edge_box_2 and right_edge_box_1 >= right_edge_box_2):
        return True
    else:
        return False


def put_box_in_package(shipping_dict, box_index, package_id):
    """
    assign random coordinates to box inside package
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]}
    :param box_index: index of a box to be moved
    :param package_id: id of a package where to put box
    :return: updated shipping_dict
    """
    boxes_df = shipping_dict['boxes']
    packages_df = shipping_dict['packages']
    # list boxes from package with package_id
    boxes_list = []
    for box in boxes_df:
        if box['package_id'] == package_id:
            boxes_list.append(box)
    #    boxes_list = [box.to_dict('list') for index, box in boxes_df.iterrows() if box['package_id'] == package_id]
    # find box with box_index
    box_to_move = get_box(box_index, boxes_df)
    # update box's package_id
    box_to_move['package_id'] = package_id
    # generate random x coordinate of box center
    package_length = [package['dimension_x'] for package in packages_df if package['package_id'] == package_id][0]
    box_to_move['x_center'] = np.random.uniform(box_to_move['dimension_x'] / 2.0,
                                                package_length - box_to_move['dimension_x'] / 2.0)
    # boxes in package that intersect with box_to_move in x direction
    intersect_boxes = []
    for box in boxes_list:
        if box['box_index'] == box_to_move["box_index"]:
            continue
        if if_intersect(box_to_move, box):
            intersect_boxes.append(box)
    if len(intersect_boxes) > 0:
        # put on top of highest box
        # print("intersected boxes:------")
        # print(intersect_boxes)
        y_top = max([(box['y_center'] + box['dimension_y'] / 2.0) for box in intersect_boxes])
        box_to_move['y_center'] = y_top + box_to_move['dimension_y'] / 2.0
        # print(box_to_move)
        # print("------------------------")
    else:
        # put on bottom of the package
        box_to_move['y_center'] = box_to_move['dimension_y'] / 2.0  # put on bottom of the package
    updated_boxes = []
    for index in range(len(boxes_df)):
        row = boxes_df[index]
        if row['box_index'] == box_to_move['box_index']:
            updated_boxes.append(box_to_move)
        else:
            updated_boxes.append(row)
    shipping_dict['boxes'] = updated_boxes
    return shipping_dict


def if_box_fits_to_shipping(shipping_dict, box):
    return True


def get_box(box_index, boxes_df):
    """
    return box from boxes_df stored with box_index
    :param box_index:
    :param boxes_df:
    :return:
    """
    return [b for b in boxes_df if b['box_index'] == box_index][0]


def pack_boxes_randomly(shipping_dict):
    """
    pack boxes in packages in random order,
    if next box doesn't fit into a package anymore,
    new packages of a random type is taken
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :return: updated shipping_dic
    """
    boxes_df = shipping_dict['boxes']

    random_box_index_list = np.random.permutation([b['box_index'] for b in boxes_df])
    for box_index in random_box_index_list:
        packages_df = shipping_dict['packages']
        box = get_box(box_index, boxes_df)
        # pick package where to put box
        if len(packages_df) == 0:
            # if shipping_dic doesn't have any packages yet, pick a type of a package randomly, but so box would fit
            package_type_to_fill = pick_package_type(box)
            # add new package to shipping
            shipping_dict = add_package(shipping_dict, package_type_to_fill)
            # put box to package into a lower left corner
            package_id = 1
        else:
            if not if_box_fits_to_shipping(shipping_dict, box):  # check if there is space left in existing packages
                # if no space, add new random package
                package_type_to_fill = pick_package_type(box)
                shipping_dict = add_package(shipping_dict, package_type_to_fill)
                package_id = max([pack["package_id"] for pack in packages_df]) + 1
            else:
                # pick a random package out of existing, but so box would fit
                package_id = pick_package_for_box(box, shipping_dict)

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
     'packages': # list of dictionaries with keys {'package_id':,'package_type':,'dimension_x':,'dimension_y':}
     'boxes': # list of dictionaries with keys  {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':,'rotated':,
                'x_center': , 'y_center':}
    """
    shipping_dict = dict(columns=['area', 'n_packages', 'packages', 'boxes'],
                         dtype=[float, int, list, list])
    shipping_dict['area'] = 0
    shipping_dict['n_packages'] = 0
    shipping_dict['packages'] = []

    # Add boxes for shipping:
    boxes_df = get_boxes(filename)
    shipping_dict['boxes'] = boxes_df
    # Pack boxes randomly
    shipping_dict = pack_boxes_randomly(shipping_dict)

    return shipping_dict
