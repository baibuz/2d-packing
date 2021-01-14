# This is the main python script for 2D packing problem with Metropolis Monte Carlo algorithm
# by E. Baibuz
from packing import *
import time
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    input_file_boxes = 'task1 - ideal packaging.xlsx'
    package_types = {'package_type1': [800, 1200],
                     'package_type2': [800, 600]} # dictionary of available package types with dimensions in cm
    shipping = initialize_shipping(input_file_boxes)
    visualise_shipping(shipping)
    start = time.time()
    shipping = packing_with_monte_carlo(shipping)
    print('time to pack with MC:', time.time()-start, 'sec')
    visualise_shipping(shipping)
