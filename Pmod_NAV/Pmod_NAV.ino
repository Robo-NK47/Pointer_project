/************************************************************************
  Wiring
  Module<--------------------> Arduino
  J1 pin 6 (3V3)     to        3V3
  J1 pin 5 (GND)     to        GND
  J1 pin 4 (SCK)     to        A5 (SCL)
  J1 pin 2 (SDI)     to        A4 (SDA)
************************************************************************/
// The earth's magnetic field varies according to its location.
// Add or subtract a constant to get the right value
// of the magnetic field using the following site
// http://www.ngdc.noaa.gov/geomag-web/#declination

#define DECLINATION 5.1 // declination (in degrees) in Cluj-Napoca (Romania).

/************************************************************************/

#define PRINT_CALCULATED  //print calculated values
//#define PRINT_RAW       //print raw data


// Call of libraries
#include <Wire.h>
#include <SparkFunLSM9DS1.h>

// defining module addresses
#define LSM9DS1_M 0x1E  //magnetometer
#define LSM9DS1_AG 0x6B //accelerometer and gyroscope

LSM9DS1 imu; // Creation of the object

void setup(void)
{
  Serial.begin(115200); // initialization of serial communication
  Wire.begin();     //initialization of the I2C communication
  imu.settings.device.commInterface = IMU_MODE_I2C; // initialization of the module
  imu.settings.device.mAddress = LSM9DS1_M;        //setting up addresses
  imu.settings.device.agAddress = LSM9DS1_AG;
  if (!imu.begin()) //display error message if that's the case
  {
    Serial.println("Communication problem.");
    while (1);
  }
}

void loop()
{
  //measure
  if ( imu.gyroAvailable() )
  {
    imu.readGyro(); //measure with the gyroscope
  }
  if ( imu.accelAvailable() )
  {
    imu.readAccel(); //measure with the accelerometer
  }
  if ( imu.magAvailable() )
  {
    imu.readMag(); //measure with the magnetometer
  }

  //display data
  printGyro(); // Print "G: gx, gy, gz"
  printAccel(); // Print "A: ax, ay, az"
  printMag(); // Print "M: mx, my, mz"
  Serial.println();
}


void printGyro()
{
float array1[] = {1000001.0, imu.calcGyro(imu.gx), imu.calcGyro(imu.gy), imu.calcGyro(imu.gz)};
byte *p = (byte*)array1;
for(byte i = 0; i < sizeof(array1); i++)
{
 Serial.write(p[i]);
}
}

void printAccel()
{
float array2[] = {1000002.0, imu.ax, imu.ay, imu.az};
byte *p = (byte*)array2;
for(byte i = 0; i < sizeof(array2); i++)
{
 Serial.write(p[i]);
}
}

void printMag()
{
float array3[] = {1000003.0, imu.calcMag(imu.mx), imu.calcMag(imu.my), imu.calcMag(imu.mz)};
byte *p = (byte*)array3;
for(byte i = 0; i < sizeof(array3); i++)
{
 Serial.write(p[i]);
}
}
