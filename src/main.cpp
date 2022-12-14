/*
 Basic B-L475E-IOT01A MQTT example
 This example is based on the mqtt_esp8266 provided with PubSubClient library.
 This sketch demonstrates the capabilities of the pubsub library in combination
 with the B-L475E-IOT01A board.
 It connects to an MQTT server then:
  - publishes "hello world" to the topic "outTopic" every two seconds
  - subscribes to the topic "inTopic", printing out any messages
    it receives. NB - it assumes the received payloads are strings not binary
  - If the first character of the topic "inTopic" is an 1, switch ON the LED_BUILTIN Led,
    else switch it off
 It will reconnect to the server if the connection is lost using a blocking
 reconnect function. See the 'mqtt_reconnect_nonblocking' example for how to
 achieve the same result without blocking the main loop.
*/
#include <SPI.h>
#include <WiFiST.h>
#include <PubSubClient.h>

// Update these with values suitable for your network.
char ssid[] = "Klinsc";
const char *password = "11111111";
const char *mqtt_server = "broker.hivemq.com";
const char *mqtt_door = "/19c21604/door";
const char *mqtt_loading = "/19c21604/loading";

// Initialize the Ethernet client object
SPIClass SPI_3(PC12, PC11, PC10);
WiFiClass WiFi(&SPI_3, PE0, PE1, PE8, PB13);
WiFiClient STClient;
int status = WL_IDLE_STATUS; // the Wifi radio's status
PubSubClient client(STClient);
long lastMsg = 0;
char msg[50];
long value = 0;

void setup_wifi()
{

  delay(10);

  // initialize the WiFi module:
  if (WiFi.status() == WL_NO_SHIELD)
  {
    Serial.println("WiFi module not detected");
    // don't continue:
    while (true)
      ;
  }

  // print firmware version:
  String fv = WiFi.firmwareVersion();
  Serial.print("Firmware version: ");
  Serial.println(fv);

  if (fv != "C3.5.2.3.BETA9")
  {
    Serial.println("Please upgrade the firmware");
  }

  // attempt to connect to Wifi network:
  Serial.print("Attempting to connect to network: ");
  Serial.println(ssid);
  while (status != WL_CONNECTED)
  {
    Serial.print(".");
    // Connect to WPA2 network:
    status = WiFi.begin(ssid, password);
    if (status != WL_CONNECTED)
    {
      // Connect to WPA (TKIP) network:
      status = WiFi.begin(ssid, password, ES_WIFI_SEC_WPA);
    }
    // wait 3 seconds for connection:
    delay(3000);
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  digitalWrite(PC9, HIGH);
}

// callback function for the MQTT client
void callback(char *topic, byte *payload, unsigned int length)
{
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");

  // define a string to hold the message:
  String message = "";
  // add each byte to the string:

  for (int i = 0; i < length; i++)
  {
    message += (char)payload[i];
  }

  Serial.println(message);

  // If payload message is "#on", turn the LED on
  if (message == "#open")
  {
    Serial.println("Open the door");
    digitalWrite(PA5, LOW);
    digitalWrite(PB14, HIGH);
    client.publish(mqtt_loading, "false");
  }
  // If payload message is "#off", turn the LED off
  if (message == "#close")
  {
    Serial.println("Close the door");
    digitalWrite(PA5, HIGH);
    digitalWrite(PB14, LOW);
    client.publish(mqtt_loading, "false");
  }
}

// reconnect to the MQTT server
void reconnect()
{
  // Loop until we're reconnected
  while (!client.connected())
  {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("B-L475E-IOT01AClient"))
    {
      Serial.println("connected");

      // ... and resubscribe
      client.subscribe(mqtt_door);
    }
    else
    {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

// initialize the system
void setup()
{
  pinMode(PA5, OUTPUT);  // Initialize the LED_BUILTIN pin as an output
  pinMode(PB14, OUTPUT); // Initialize the LED_BUILTIN pin as an output

  pinMode(PC13, INPUT_PULLUP); // if press the button toggle the LED

  pinMode(PA5, OUTPUT);
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

// main loop after initialization
void loop()
{
  if (!client.connected())
  {
    Serial.println("Disconnected");
    reconnect();
  }
  client.loop();

  if (digitalRead(PC13) == LOW)
  {
    client.publish(mqtt_door, "#close");
  }
}