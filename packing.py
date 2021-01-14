import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import copy

global packages_dimensions, input_file_boxes, precision
package_types = {'package_type1': [800, 1200],
                 'package_type2': [800, 600]}  # dictionary of available package types with dimensions in cm
precision: float = 1.0  # precision of coordinates

seed = 1
np.random.seed(seed)
# np.random.seed(None)
print('seed = ', np.random.get_state()[1][0])

# Metpolis Monte Carlo simulated annealing parameters.
global c0
c0 = 10000  # initial value of control parameter
alpha = 0.5  # cooling parameter
# alpha = 0.0002
c_min = 2  # minimal value of control parameter
max_number_steps = 1000  # maximum number of steps for every cooling parameter


def get_box(box_index, boxes_df):
    """
    return box from boxes_df stored with box_index
    :param box_index:
    :param boxes_df: list of dictionaries with keys  {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':,
    'rotated':, 'x_center': , 'y_center':}
    :return:
    """
    return [b for b in boxes_df if b['box_index'] == box_index][0]


def get_package(package_id, packages_df):
    """
    return package of package_id from packages_df
    :param package_id:
    :param packages_df: list of dictionaries with keys {'package_id':,'package_type':,'dimension_x':,'dimension_y':}
    :return:
    """
    return [p for p in packages_df if p['package_id'] == package_id][0]


def get_boxes_in_package(package_id, shipping_info):
    """
    return boxes stored in package with package_id
    :param package_id:
    :param shipping_info: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :return: list of dictionaries  [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    """
    boxes = shipping_info['boxes']
    return [box for box in boxes if box['package_id'] == package_id]


def get_rotated_box(box):
    """
    alternate box dimensions and return updated box
    change 'rotated' index to the opposite
    :param box: {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':, 'x_center': , 'y_center':}
    :return:updated box
    """
    box_x = box['dimension_x']
    box_y = box['dimension_y']
    box['dimension_x'] = box_y
    box['dimension_y'] = box_x
    if box['rotated'] == 'Not rotated':
        box['rotated'] = 'Rotated'
    else:
        box['rotated'] = 'Not rotated'
    return box


def if_box_fits_to_empty_package(box_dimension_x, box_dimension_y, package_type):
    """
    This function check if a box of certain dimensions fits to package of package_type,
    box can be rotated
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


def if_package_empty(package_id, shipping_dict):
    """
    check if package is empty
    :param package_id: id of package to be checked
    :param shipping_dict:
    :return: True if package is empty; False if there is at least one box in a package
    """

    boxes = get_boxes_in_package(package_id, shipping_dict)
    if len(boxes) == 0:
        return True
    else:
        return False


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
    :return: list of dictionaries with following columns:
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


def pick_package(packages_df):
    """
    randomly pick a package form the dictionary
    :param packages_df: list of dictionaries [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :return: package dictionary {'package_id':,'package_type':,'dimension_x':,'dimension_y':}
    """
    if len(packages_df) == 0:
        print("No packages to pick from shipping_dict, exit")
        return False
    ind = np.random.randint(0, len(packages_df))
    package = packages_df[ind]
    return package


def update_shipping_with_box(box, shipping_dict):
    """
    modifies shipping dictionary by adding box
    :param box: {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}
    :param shipping_dict: shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :return:
    """
    boxes_df = copy.deepcopy(shipping_dict['boxes'])
    # update shipping_dict with new box
    updated_boxes = []
    for index in range(len(boxes_df)):
        row = boxes_df[index]
        if row['box_index'] == box['box_index']:
            updated_boxes.append(copy.deepcopy(box))
        else:
            updated_boxes.append(copy.deepcopy(row))
    shipping_dict['boxes'] = updated_boxes
    return shipping_dict


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
    boxes_df = shipping_dict['boxes']
    box_to_fit = get_box(box_index, boxes_df)
    packages_df = shipping_dict['packages']
    package = get_package(package_id, packages_df)
    if box_to_fit['dimension_x'] > package['dimension_x']:
        return False
    # list boxes that are already in package_id
    boxes_in_package = get_boxes_in_package(package_id, shipping_dict)
    # list coordinates of tops of boxes and find maximum
    max_top_y_of_boxes = max([box['y_center'] + box['dimension_y'] / 2.0 for box in boxes_in_package])
    # check if highest box top + height of box to fit is less than package height
    if max_top_y_of_boxes + box_to_fit['dimension_y'] <= package['dimension_y']:
        return True
    else:
        return False


def pick_package_for_box(box, shipping_dict):
    """
    This function picks a random package from one of the packages in shipping_dict that satisfy condition that box
    fits to package dimension, returns id of a package
    :param shipping_dict: dictionary with a shipping info in a
    format: {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]]
    :param box: dictionary with keys  {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':,
    'rotated':,'x_center': , 'y_center':}
    :return: package_id - id of a package where to put box
    """
    picked = False
    while not picked:
        package = pick_package(shipping_dict['packages'])
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


def remove_empty_package(package_id, shipping_dict):
    """
    checks that package is empty,
    remove package of package_id from shipping_dict
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]}
    :param package_id: id of package to be removed
    :return: updated shipping_dict, False if package is not empty
    """
    packages_df = copy.deepcopy(shipping_dict['packages'])
    boxes_df = shipping_dict['boxes']
    if not if_package_empty(package_id, shipping_dict):
        print("Error: empty package to be removed is not empty. Exit ")
        return False

    updated_packages = []
    for index in range(len(packages_df)):
        row = packages_df[index]
        if row['package_id'] != package_id:
            updated_packages.append(row)
    shipping_dict['packages'] = updated_packages
    return shipping_dict


def if_intersect_x(box_1, box_2):
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


def if_intersect_y(box_1, box_2):
    """
   return True if box_1 intersect with box_2 in y direction
   :param box_1: {['box_index', 'dimension_x', 'dimension_y','package_id','rotated', 'x_center' , 'y_center']}
   :param box_2: {['box_index', 'dimension_x', 'dimension_y','package_id','rotated', 'x_center' , 'y_center']}
   :return: True of False
   """
    right_edge_box_1 = box_1['y_center'] + box_1['dimension_y'] / 2.0
    left_edge_box_1 = box_1['y_center'] - box_1['dimension_y'] / 2.0
    right_edge_box_2 = box_2['y_center'] + box_2['dimension_y'] / 2.0
    left_edge_box_2 = box_2['y_center'] - box_2['dimension_y'] / 2.0
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
    assign random x coordinates to box inside package, no checks performed on wether box fits to package
    put box on top of another box if there is another box in x coordinate
    box is not rotated inside function
    coordinates are assigned within precision stored in global variable precision
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
    boxes_list = get_boxes_in_package(package_id, shipping_dict)
    # find box with box_index
    box_to_move = get_box(box_index, boxes_df)
    # update box's package_id
    box_to_move['package_id'] = package_id
    # generate random x coordinate of box center
    package_length = [package['dimension_x'] for package in packages_df if package['package_id'] == package_id][0]

    available_x_center = np.arange(box_to_move['dimension_x'] / 2.0,
                                   package_length - box_to_move['dimension_x'] / 2.0 + precision,
                                   precision)
    box_to_move['x_center'] = np.random.choice(available_x_center)
    # boxes in package that intersect with box_to_move in x direction
    intersect_boxes = []
    for box in boxes_list:
        if box['box_index'] == box_to_move["box_index"]:
            continue
        if if_intersect_x(box_to_move, box):
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


def move_box_in_same_package(shipping_dict, box_index):
    '''
    assign random x and y coordinates within package borders
    :param shipping: shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :param box_index: index of the box to be moved
    :return:
    '''
    boxes_df = copy.deepcopy(shipping_dict['boxes'])
    packages_df = shipping_dict['packages']
    box_to_move = get_box(box_index, boxes_df)
    package_id = box_to_move['package_id']
    # generate random x coordinate within package borders
    package_length = [package['dimension_x'] for package in packages_df if package['package_id'] == package_id][0]
    available_x_center = np.arange(box_to_move['dimension_x'] / 2.0,
                                   package_length - box_to_move['dimension_x'] / 2.0 + precision,
                                   precision)
    box_to_move['x_center'] = np.random.choice(available_x_center)
    # generate random y coordinate within package borders
    package_width = [package['dimension_y'] for package in packages_df if package['package_id'] == package_id][0]
    available_y_center = np.arange(box_to_move['dimension_y'] / 2.0,
                                   package_width - box_to_move['dimension_y'] / 2.0 + precision,
                                   precision)
    box_to_move['y_center'] = np.random.choice(available_y_center)
    shipping_dict = update_shipping_with_box(box_to_move, shipping_dict)
    return copy.deepcopy(shipping_dict)


def move_box_to_random_package(shipping_dict, box_index):
    '''
    assign random x and y coordinates in random package
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :param box_index: index of the box to be moved
    :return:
    '''

    boxes_df = copy.deepcopy(shipping_dict['boxes'])
    packages_df = shipping_dict['packages']

    box_to_move = get_box(box_index, boxes_df)
    package_original = box_to_move['package_id']
    random_package_id = package_original
    while package_original == random_package_id:  # make sure that picked package is not the same where the box already is
        random_package = pick_package(packages_df)
        random_package_id = random_package['package_id']

    # generate random x coordinate within package borders
    package_length = [package['dimension_x'] for package in packages_df if package['package_id'] == random_package_id][
        0]
    available_x_center = np.arange(box_to_move['dimension_x'] / 2.0,
                                   package_length + precision,
                                   precision)
    box_to_move['x_center'] = np.random.choice(available_x_center)
    # generate random y coordinate within package borders
    package_height = [package['dimension_y'] for package in packages_df if package['package_id'] == random_package_id][
        0]
    available_y_center = np.arange(box_to_move['dimension_y'] / 2.0,
                                   package_height + precision,
                                   precision)
    box_to_move['package_id'] = random_package_id
    box_to_move['y_center'] = np.random.choice(available_y_center)
    shipping_dict = update_shipping_with_box(box_to_move, shipping_dict)

    return copy.deepcopy(shipping_dict)


def rotate_box(shipping_dict, box_index):
    """
    rotate
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :param box_index: index of the box to be moved
    :return: updated shipping_dict
    """
    boxes_df = copy.deepcopy(shipping_dict['boxes'])
    box_to_rotate = get_box(box_index, boxes_df)
    rotated_box = get_rotated_box(box_to_rotate)

    # update shipping_dict with new box
    shipping_dict = update_shipping_with_box(rotated_box, shipping_dict)

    return shipping_dict


def swap_boxes_same_container(box_1_index, box_2_index, shipping_dict):
    """
    swap coordinates of two boxes in the same container
    :param box_1_index:
    :param box_2_index:
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :return: updated shipping_dict
    """
    box_1 = get_box(box_1_index, shipping_dict['boxes'])
    box_2 = get_box(box_2_index, shipping_dict['boxes'])
    if box_1['package_id'] != box_2['package_id']:
        print(" in swap_boxes_same_container: package id is not the same. Exit")
        return False
    box_1_x_center = box_1['x_center']
    box_2_x_center = box_2['x_center']
    box_1_y_center = box_1['y_center']
    box_2_y_center = box_2['y_center']
    box_1['x_center'] = box_2_x_center
    box_1['y_center'] = box_2_y_center
    box_2['x_center'] = box_1_x_center
    box_2['y_center'] = box_1_y_center
    shipping_dict = update_shipping_with_box(box_1, shipping_dict)
    shipping_dict = update_shipping_with_box(box_2, shipping_dict)

    return shipping_dict


def swap_boxes(box_1_index, box_2_index, shipping_dict):
    """
    swap coordinates of two boxes
    :param box_1_index: index of box 1
    :param box_2_index: index of box 2
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :return: updated shipping_dict
    """
    box_1 = get_box(box_1_index, shipping_dict['boxes'])
    box_2 = get_box(box_2_index, shipping_dict['boxes'])
    box_1_package = box_1['package_id']
    box_2_package = box_2['package_id']

    box_1_x_center = box_1['x_center']
    box_2_x_center = box_2['x_center']
    box_1_y_center = box_1['y_center']
    box_2_y_center = box_2['y_center']
    box_1['x_center'] = box_2_x_center
    box_1['y_center'] = box_2_y_center
    box_2['x_center'] = box_1_x_center
    box_2['y_center'] = box_1_y_center
    box_1['package_id'] = box_2_package
    box_2['package_id'] = box_1_package
    shipping_dict = update_shipping_with_box(box_1, shipping_dict)
    shipping_dict = update_shipping_with_box(box_2, shipping_dict)
    return shipping_dict


def if_box_fits_to_shipping(box, shipping_dict):
    """
    return True if box fits to at least one package in shipping_dict
    :param box: {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}
    :param shipping_dict: dictionary with a shipping info in a format:
    {'area':a, 'n_packages':n,'packages': [{'package_id':,'package_type':,'dimension_x':,'dimension_y':}],
    'boxes': [{'box_index':, 'dimension_x':, 'dimension_y':,'package_id':, 'rotated':,'x_center': , 'y_center':}]
    :return: True or False
    """
    packages = shipping_dict['packages']
    for package in packages:
        if if_box_fits_to_package(box['box_index'], package['package_id'], shipping_dict):
            return True
    return False

    return True


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
            if not if_box_fits_to_shipping(box, shipping_dict):  # check if there is space left in existing packages
                # if no space, add new random package
                package_type_to_fill = pick_package_type(box)
                shipping_dict = add_package(shipping_dict, package_type_to_fill)
                package_id = max([pack["package_id"] for pack in shipping_dict['packages']])
            else:
                # pick a random package out of existing, but so box would fit
                package_id = pick_package_for_box(box, shipping_dict)
        # put box of box_index
        # check if box needs to be rotated before put to package_id
        package = get_package(package_id, shipping_dict['packages'])
        if box['dimension_x'] > package['dimension_x'] or box['dimension_y'] > package['dimension_y']:
            rotated_box = get_rotated_box(box)
            # update shipping_dict with new set of boxes
            updated_boxes = []
            for b in boxes_df:
                if b['box_index'] == rotated_box['box_index']:
                    updated_boxes.append(rotated_box)
                else:
                    updated_boxes.append(b)
            shipping_dict['boxes'] = updated_boxes
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


def if_shipping_valid(shipping_dict):
    """
    return True if boxes in packages don't intersect with each other and
    if all boxes are withing corresponding package dimensions
    :param shipping_dict: dictionary {'area': overall area occupied by all packages, 'n_packages': number of packages,
     'packages': # list of dictionaries with keys {'package_id':,'package_type':,'dimension_x':,'dimension_y':},
     'boxes': # list of dictionaries with keys  {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':,'rotated':,
                'x_center': , 'y_center':}
    :return: True or False
    """
    # check each package
    packages = shipping_dict['packages']

    for package in packages:
        boxes_in_package = get_boxes_in_package(package['package_id'], shipping_dict)
        for box in boxes_in_package:
            if box['x_center'] - box['dimension_x'] / 2.0 < 0.0 or \
                    box['x_center'] + box['dimension_x'] / 2.0 > package['dimension_x'] or \
                    box['y_center'] - box['dimension_y'] / 2.0 < 0.0 or \
                    box['y_center'] + box['dimension_y'] / 2.0 > package['dimension_y']:
                return False
            for box2 in boxes_in_package:
                if box['box_index'] == box2['box_index']:
                    continue
                if if_intersect_x(box, box2):  # if boxes intersect in x direction
                    if if_intersect_y(box, box2):  # check y direction
                        return False
    return True


def change_shipping_randomly(shipping_dict):
    """
    1. randomly perform one of the modifications in shipping:
    - move box to random x coordinate in the same package, put on top of highest box below
    - move box to random x coordinate in random package, put on top of highest box below
    - rotate random box
    - swap x coordinates of two random boxes in the same container, y coordinates are recalculated
    - swap x coordinates of two random boxes from different containers, y coordinates are recalculated
    2. reject modification if any boxes in updated shipping are outside of container or intersect with each other
    3. remove any empty packages
    4. update shipping area
    4. if modification accepted, modify shipping_dict
    :param shipping_dict: dictionary with initial arrangement {'area': overall area occupied by all packages,
    'n_packages': number of packages,
     'packages': # list of dictionaries with keys {'package_id':,'package_type':,'dimension_x':,'dimension_y':}
     'boxes': # list of dictionaries with keys  {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':,'rotated':,
                'x_center': , 'y_center':}
    :return: shipping_dict , updated if  modification was accepted
    """
    # perform one of the modifications in shipping
    n_permitted_moves = 5
    rndn = np.random.randint(0, n_permitted_moves)
    random_box_index = np.random.choice([b['box_index'] for b in shipping_dict['boxes']])
    random_box = get_box(random_box_index, shipping_dict['boxes'])
    random_box_package_id = random_box['package_id']
    if rndn == 0:
        # move random box to random x coordinate in the same package, put on top of highest box below
        shipping_dict = move_box_in_same_package(shipping_dict, random_box_index)
    elif rndn == 1:
        # move random box to another random package, put on top of highest box below
        shipping_dict = move_box_to_random_package(shipping_dict, random_box_index)
    elif rndn == 2:
        # rotate box
        shipping_dict = rotate_box(shipping_dict, random_box_index)
    elif rndn == 3:
        # swap two boxes in the same package
        # are there other boxes in package:
        boxes_in_package = get_boxes_in_package(random_box_package_id, shipping_dict)
        if len(boxes_in_package) > 1:
            indexes = [b['box_index'] for b in boxes_in_package if b['box_index'] != random_box_index]
            random_box_2_index = np.random.choice(indexes)
            shipping_dict = swap_boxes_same_container(random_box_index, random_box_2_index, shipping_dict)

    elif rndn == 4:

        # swap two boxes from different packages
        indexes = [b['box_index'] for b in shipping_dict['boxes'] if b['box_index'] != random_box_index]
        random_box_2_index = np.random.choice(indexes)
        shipping_dict = swap_boxes(random_box_index, random_box_2_index, shipping_dict)
    '''
    elif rndn == 5:
        # add a new container of random type
    '''
    # 4. update shipping area
    shipping_dict['area'] = calculate_area_packages(shipping_dict['packages'])
    return shipping_dict


def maxwell_distribution(delta, c):
    """
    calculates maxwell distribution for a given change in cost function
    :param delta: change in cost function (area in 2D packing)
    :param c: control parameter (or temperature)
    :return: exp(-delta/c)
    """
    return np.exp(-delta / c)


def packing_with_monte_carlo(shipping_dict):
    """
    optimize arrangement of boxes in packages with Metropolis Monte Carlo simulated annealing method
    uses global variable:
    :param shipping_dict: dictionary with initial arrangement {'area': overall area occupied by all packages,
    'n_packages': number of packages,
     'packages': # list of dictionaries with keys {'package_id':,'package_type':,'dimension_x':,'dimension_y':}
     'boxes': # list of dictionaries with keys  {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':,'rotated':,
                'x_center': , 'y_center':}
    :return: updated shipping_dict
    """
    current_shipping = copy.deepcopy(shipping_dict)
    c = c0
    while c >= c_min:  # loop over control parameter
        # perform max_number_steps for each cooling parameter
        for step_counter in range(max_number_steps):
            area_before_change = current_shipping['area']
            shipping_dict_modified = {}
            shipping_dict_modified = copy.deepcopy(current_shipping)
            shipping_dict_modified = change_shipping_randomly(shipping_dict_modified)  # randomly modify shipping
            # 2. reject modification if any boxes in updated shipping are outside of container or intersect with each other

            if not if_shipping_valid(shipping_dict_modified):
                # if random move was not accepted because box was put into occupied space or outside the package
                # continue to next step without accepting the modification
                continue
            else:
                # 2. remove any empty containers
                for package in shipping_dict_modified['packages']:
                    if if_package_empty(package['package_id'], shipping_dict_modified):
                        shipping_dict_modified = remove_empty_package(package['package_id'], shipping_dict_modified)
                area_after_change = shipping_dict_modified['area']
                if area_after_change <= area_before_change:
                    # if area of packages became smaller (package was removed) or stayed the same, update shipping_dic
                    current_shipping = {}
                    current_shipping = copy.deepcopy(shipping_dict_modified)
                else:
                    # if empty area in packages became larger,
                    # accept or reject the move with the probability, according to Maxwell distribution

                    #calculate_empty_area


                    u = np.random.random_sample()
                    f = maxwell_distribution(area_after_change - area_before_change, c)
                    if u < f:
                        # accepted
                        current_shipping = {}
                        current_shipping = copy.deepcopy(shipping_dict_modified)

        c = alpha * c
    shipping_dict = []
    shipping_dict = copy.deepcopy(current_shipping)
    return current_shipping


def visualise_shipping(shipping_dict):
    """
    plot packages and boxes from shipping_dict
    :param shipping_dict: {'area': overall area occupied by all packages,
    'n_packages': number of packages,
     'packages': # list of dictionaries with keys {'package_id':,'package_type':,'dimension_x':,'dimension_y':}
     'boxes': # list of dictionaries with keys  {'box_index':, 'dimension_x':, 'dimension_y':,'package_id':,'rotated':,
                'x_center': , 'y_center':}
    """

    fig = plt.figure()
    ax = fig.add_subplot(111)

    gap: float = 50.0
    # plt.axis("off")
    x_start = 0.0
    y_start = 0.0

    for package in shipping_dict['packages']:
        # plot package one after another with a gap
        package_width = package['dimension_x']
        package_height = package['dimension_y']
        rect = matplotlib.patches.Rectangle((x_start, y_start), package_width, package_height,
                                            fc='royalblue', edgecolor='k', linewidth=1)
        ax.add_patch(rect)
        boxes = get_boxes_in_package(package['package_id'], shipping_dict)
        for box in boxes:
            # plot boxes inside package one after another
            box_width = box['dimension_x']
            box_height = box['dimension_y']
            x_center = box['x_center']
            y_center = box['y_center']
            box_x_start = x_start + x_center - box_width / 2.0
            box_y_start = y_start + y_center - box_height / 2.0
            if box['rotated'] == 'Rotated':
                color = 'firebrick'
            else:
                color = 'gold'
            rect = matplotlib.patches.Rectangle((box_x_start, box_y_start), box_width, box_height,
                                                fc=color, edgecolor='k', linewidth=0.5, label=box['box_index'])
            plt.text(box_x_start + box_width / 2.0, box_y_start + box_height / 2.0, box['box_index'], fontsize=5)
            ax.add_patch(rect)

        x_start += package_width + gap
    figure_width = x_start + package_width + gap
    figure_height = max([package['dimension_y'] for package in shipping_dict['packages']]) + gap
    plt.xlim([-gap, figure_width])
    plt.ylim([-gap, figure_height])

    plt.show()
