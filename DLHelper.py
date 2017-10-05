import h5py
from PIL import Image
from six.moves import cPickle
import csv, time, os.path
import matplotlib.pyplot as plt
import numpy as np

# function for reading the images
# arguments: path to the traffic sign data, for example './GTSRB/Training'
# returns: list of images, list of corresponding labels 
def readTrafficSigns(rootpath, size, training=True):
    '''Reads traffic sign data for German Traffic Sign Recognition Benchmark.

    Arguments: path to the traffic sign data, for example './GTSRB/Training'
    Returns:   list of images, list of corresponding labels'''
    images = [] # images
    labels = [] # corresponding labels
    # loop over all 43 classes
    if training:
        for c in range(0,43):
            prefix = rootpath + '/' + format(c, '05d') + '/' # subdirectory for class
            gtFile = open(prefix + 'GT-'+ format(c, '05d') + '.csv') # annotations file
            gtReader = csv.reader(gtFile, delimiter=';') # csv parser for annotations file
            next(gtReader) # skip header
            # loop over all images in current annotations file
            for row in gtReader:
#                 image = Image.open(prefix + row[0]).convert('L') # Load an image and convert to grayscale
                image = Image.open(prefix + row[0])
                box = (int(row[3]), int(row[4]), int(row[5]), int(row[6])) # Specify ROI box
                image = image.crop(box) # Crop the ROI
                image = image.resize(size) # Resize images
                images.append(np.asarray(image).astype('uint8')) # the 1th column is the filename, while 3,4,5,6 are the vertices of ROI
                labels.append(int(row[7])) # the 8th column is the label
            gtFile.close()
    else:
        gtFile = open(rootpath + "/../../GT-final_test.csv") # annotations file
        gtReader = csv.reader(gtFile, delimiter=';') # csv parser for annotations file
        next(gtReader) # skip header
        # loop over all images in current annotations file
        for row in gtReader:
#             image = Image.open(rootpath + '/' + row[0]).convert('L') # Load an image and convert to grayscale
            image = Image.open(rootpath + '/' + row[0]) # Color version
            box = (int(row[3]), int(row[4]), int(row[5]), int(row[6])) # Specify ROI box
            image = image.crop(box) # Crop the ROI
            image = image.resize(size) # Resize images
            images.append(np.asarray(image).astype('uint8')) # the 1th column is the filename, while 3,4,5,6 are the vertices of ROI
            labels.append(int(row[7])) # the 8th column is the label
        gtFile.close()
        
    return images, labels

def getImageSets(root, resize_size):
    train_dir = root + "/Final_Training/Images"
    test_dir = root + "/Final_Test/Images"

    ## If pickle file exists, read the file
    if os.path.isfile(root + "/processed_images.pkl"):
        f = open(root + "/processed_images.pkl", 'rb')
        trainImages = cPickle.load(f, encoding="latin1")
        trainLabels = cPickle.load(f, encoding="latin1")
        testImages = cPickle.load(f, encoding="latin1")
        testLabels = cPickle.load(f, encoding="latin1")
        f.close()
    ## Else, read images and write to the pickle file
    else:
        start = time.time()
        trainImages, trainLabels = readTrafficSigns(train_dir, resize_size)
        print("Training Image preprocessing finished in {:.2f} seconds".format(time.time() - start))

        start = time.time()
        testImages, testLabels = readTrafficSigns(test_dir, resize_size, False)
        print("Testing Image preprocessing finished in {:.2f} seconds".format(time.time() - start))
        
        f = open(root + "/processed_images.pkl", 'wb')

        for obj in [trainImages, trainLabels, testImages, testLabels]:
            cPickle.dump(obj, f, protocol=cPickle.HIGHEST_PROTOCOL)
        f.close()

    print(trainImages[42].shape)
    # plt.imshow(trainImages[42])
    # plt.show()

    print(testImages[21].shape)
    # plt.imshow(trainImages[21])
    # plt.show()

    return trainImages, trainLabels, testImages, testLabels

def init_h5py(filename, epoch_num, max_total_batch):
    f = h5py.File(filename, 'w')
        
    try:
        # config group for some common params
        config = f.create_group('config')
        config.attrs["total_epochs"] = epoch_num

        # cost group for training and validation cost
        cost = f.create_group('cost')
        loss = cost.create_dataset('loss', (epoch_num,))
        loss.attrs['time_markers'] = 'epoch_freq'
        loss.attrs['epoch_freq'] = 1
        train = cost.create_dataset('train', (max_total_batch,)) # Set size to maximum theoretical value
        train.attrs['time_markers'] = 'minibatch'

        # time group for batch and epoch time
        t = f.create_group('time')
        loss = t.create_dataset('loss', (epoch_num,))
        train = t.create_group('train')
        start_time = train.create_dataset("start_time", (1,))
        start_time.attrs['units'] = 'seconds'
        end_time = train.create_dataset("end_time", (1,))
        end_time.attrs['units'] = 'seconds'
        train_batch = t.create_dataset('train_batch', (max_total_batch,)) # Same as above

        # accuracy group for training and validation accuracy
        acc = f.create_group('accuracy')
        acc_v = acc.create_dataset('valid', (epoch_num,))
        acc_v.attrs['time_markers'] = 'epoch_freq'
        acc_v.attrs['epoch_freq'] = 1
        acc_t = acc.create_dataset('train', (max_total_batch,))
        acc_t.attrs['time_markers'] = 'minibatch'

        # Mark which batches are the end of an epoch
        time_markers = f.create_group('time_markers')
        time_markers.attrs['epochs_complete'] = epoch_num
        train_batch = time_markers.create_dataset('minibatch', (epoch_num,))

        # Inference accuracy
        infer = f.create_group('infer_acc')
        infer_acc = infer.create_dataset('accuracy', (1,))

    except Exception as e:
        f.close() # Avoid hdf5 runtime error or os error
        raise e # Catch the exception to close the file, then raise it to stop the program

    return f