import serial
import tensorflow as tf
import time
import pandas as pd
import numpy as np
import joblib  


MODEL_PATH = "model/landslide_prediction_model.h5"  
SCALER_PATH = "model/scaler.pkl"                    
SERIAL_PORT = "COM6"                                
BAUD_RATE = 9600                                    
TIMEOUT = 1                                         
FEATURES = ["Slope", "Soil Moisture", "Barometric Pressure", "Rainfall", "Vibration"]


try:
    model = tf.keras.models.load_model(MODEL_PATH)
    print("Model loaded successfully.")
except FileNotFoundError:
    print("Error: Model file not found. Please check the MODEL_PATH.")
    exit(1)


try:
    scaler = joblib.load(SCALER_PATH)
    print("Scaler loaded successfully.")
except FileNotFoundError:
    print("Error: Scaler file not found. Please check the SCALER_PATH.")
    exit(1)


def preprocess_data(data):
    try:
        if data.startswith("*"):
            moist_normal = int(data[11:14]) - 30
            rainfall_normal = int(data[4:7]) - 60
            slope = int(data[1:4]) - 10
            barometric_pressure = data[8:11]
            vibration = data[14:]
            raw_values = [slope, moist_normal, barometric_pressure , rainfall_normal, vibration]  
            values = [float(x) for x in raw_values]  
            print("Values",values)
            if len(values) == len(FEATURES):
                input_df = pd.DataFrame([values], columns=FEATURES)

                scaled_data = scaler.transform(input_df)
                return scaled_data  
            else:
                print("Error: Expected 5 sensor values.")
                return None
        else:
            print("Error: Data does not start with '*'.")
            return None
    except ValueError as e:
        print(f"Error: Invalid data format. Ensure all values are numeric. Details: {e}")
        return None

def main():
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
            print(f"Listening to {SERIAL_PORT}... Press Ctrl+C to stop.")

            while True:
                try:
                    if ser.in_waiting > 0:  
                        raw_data = ser.readline().decode("utf-8").strip()  
                        print(f"Received data: {raw_data}")

                        input_data = preprocess_data(raw_data)
                        if input_data is not None:
                            try:
                                prediction = model.predict(input_data)[0][0]  
                                probability = float(prediction)  
                                percentage = float(prediction)*100
                                binary_prediction = int(round(probability))  

                                
                                response = f"*{binary_prediction}{percentage:.4f}"  
                                if binary_prediction == 1:
                                    print(f"Prediction: Landslide detected! Probability: {percentage:.2f} %")
                                else:
                                    print(f"Prediction: No landslide. Probability: {percentage:.2f} %")

                                print(f"Sending response: {response}")
                                ser.write(f"{response}\n".encode("utf-8"))
                            except Exception as e:
                                print(f"Error during prediction: {e}")
                    time.sleep(0.1)  
                except Exception as e:
                    print(f"Error in serial communication loop: {e}")
                    continue

    except KeyboardInterrupt:
        print("Program terminated by user.")
    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
