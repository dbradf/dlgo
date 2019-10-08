import os

import click
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Conv2D, Flatten, Dropout, MaxPooling2D

DATA_DIRECTORY = 'data'
BOARD_SIZE = 9


def load_data(data_path: str = DATA_DIRECTORY):
    x = np.load(os.path.join(data_path, "features-40k.npy"))
    y = np.load(os.path.join(data_path, "labels-40k.npy"))
    samples = x.shape[0]

    x = x.reshape(samples, BOARD_SIZE, BOARD_SIZE, 1)

    return x, y


def split_data(x, y):
    train_samples = int(0.9 * x.shape[0])
    x_train, x_test = x[:train_samples], x[train_samples:]
    y_train, y_test = y[:train_samples], y[train_samples:]

    return (x_train, x_test), (y_train, y_test)


def create_model(x_train, y_train, x_test, y_test):
    input_shape = (BOARD_SIZE, BOARD_SIZE, 1)
    model = Sequential()
    model.add(Conv2D(48, kernel_size=(3, 3), activation='relu', padding='same',
                     input_shape=input_shape))
    model.add(Dropout(rate=0.5))
    model.add(Conv2D(48, (3, 3), padding='same', activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(rate=0.5))
    model.add(Flatten())

    model.add(Dense(512, activation='relu'))
    model.add(Dropout(rate=0.5))
    model.add(Dense(BOARD_SIZE * BOARD_SIZE, activation='softmax'))
    model.summary()

    model.compile(loss='categorical_crossentropy',
                  optimizer='sgd',
                  metrics=['accuracy'])

    model.fit(x_train, y_train, batch_size=64, epochs=100, verbose=1, validation_data=[x_test, y_test])

    return model


@click.command()
def main():
    x, y = load_data()
    (x_train, x_test), (y_train, y_test) = split_data(x, y)

    model = create_model(x_train, y_train, x_test, y_test)

    score = model.evaluate(x_test, y_test, verbose=0)
    print('Test loss:', score[0])
    print('Test accuracy:', score[1])
