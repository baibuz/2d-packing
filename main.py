# This is the main python script for 2D packing problem with Metropolis Monte Carlo algorithm
# by E. Baibuz
from packing import *
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    input_file_boxes = 'task1 - ideal packaging.xlsx'
    shipping = initialize_shipping(input_file_boxes)
    visualise_shipping(shipping)
    plt.show()