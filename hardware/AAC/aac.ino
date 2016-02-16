
//Communication
#include <Ethernet.h>
#include <Wire.h>
#include <SPI.h>

//Encryption
#include <aes.h>
#include <sha256.h>
#include <sha256_config.h>
#include <cencode.h>

//Other
#include <Stepper.h>
#include <EEPROM.h>
#include <LiquidCrystal_I2C.h>
#include <Adafruit_PN532.h>
#include <string.h>

// ------------- cardBuffer settings --------------
// 2 bytes for cardBuffer current position
#define CARDBUFFER_CURR_POS 19

// cardBuffer start byte (number itself including)
#define CARDBUFFER_START 21

// cardBuffer end byte (number itself including)
// 80 bytes for card buffer
#define CARDBUFFER_END 100
// ------------- end cardbuffer settings -----------

//connectivity settings
#define HTTP_PORT 8000
// #define UDP_OUT   8010
// #define UDP_IN    8011

// ------- queue settings --------------
#define QUEUE_ITEM_COUNT 105
#define QUEUE_CURSOR_START 107
#define QUEUE_CURSOR_END 109
//500 bytes for queue
#define QUEUE_START 111
#define QUEUE_END 510
//---------- end queue settings ---------

//serial number which acts as a password
#define SN (uint8_t*) "0123456789ABCDEF"
// hardware id
#define ID "micro"

//current state of appliance, true for active, false for inactive
boolean state;
boolean busy = false;

//NFC Reader
#define PN532_IRQ   (2)
#define PN532_RESET (10)
Adafruit_PN532 nfc(PN532_IRQ,PN532_RESET);

//user card id
uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };

// queue check interval
uint16_t queue_cc = 0;

// user cards check interval
uint16_t usrc_cc = 0;

uint16_t dataStart = queue_getCursorStart();
uint16_t dataEnd = queue_getCursorEnd();
uint16_t itemCount = queue_getItemCount();

// pin for buzzer
int beepPin = 7;

//Pins for LEDS which represents on/off
int onLed = 8;
int offLed = 9;

//Connection Settings
byte mac[] = {  0x98, 0x4F, 0xEE, 0x00, 0x2C, 0xE4 }; // MAC address of board
IPAddress board(192,168,0,137); // board IP
IPAddress server(192,168,0,101); // Colemass server IP
EthernetClient client;

//Initialize LCD
LiquidCrystal_I2C lcd(0x27, 3, 2);


//Programm will try to push every 30 seconds to push data in queue to server
unsigned long currentMillis = 0;
unsigned long previousMillis;
const long interval = 30000;



void setup(void) {
  lcd.begin();
  lcd.backlight();
  lcd.print("Initializing...");


  Serial.begin(9600);
  Serial.println("Hello!");

  attachInterrupt(3, button_pressed, FALLING); // Interrupt for menu button

  pinMode(beepPin, OUTPUT);
  pinMode(onLed, OUTPUT);
  pinMode(offLed, OUTPUT);

  nfc.begin();

  // initialize NFC Reader
  uint32_t versiondata = nfc.getFirmwareVersion();
  if (! versiondata) {
    Serial.print("Didn't find PN53x board");
    while (1); // halt
  }
  // Got ok data, print it out!
  Serial.print("Found chip PN5"); Serial.println((versiondata >> 24) & 0xFF, HEX);
  Serial.print("Firmware ver. "); Serial.print((versiondata >> 16) & 0xFF, DEC);
  Serial.print('.'); Serial.println((versiondata >> 8) & 0xFF, DEC);

   // configure board to read RFID tags
   nfc.setPassiveActivationRetries(80);
   nfc.SAMConfig();

  Ethernet.begin(mac, board);

  pollCardsFromServer();

  state = getApplStatus();

   if(state){
    digitalWrite(onLed, HIGH);
    digitalWrite(offLed, LOW);
    lcd.clear();
    lcd.print("Logged in");
  }
  else{
    digitalWrite(onLed, LOW);
    digitalWrite(offLed, HIGH);
    lcd.clear();
    lcd.print("Please Swipe");
  }


  Serial.println("Everything set up");

}

void loop(void) {

  uint8_t success;
  uint8_t uidLength;                        // Length of the UID (4 or 7 bytes depending on ISO14443A card type)

  //if inactive wait for card to be swiped or a report

  if (!state && !busy){

    lcd.clear();
    lcd.print("  Swipe card to");
    lcd.setCursor(0,1);
    lcd.print("     log in");

    success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);
    if (success) {

      if (cardBuffer_isInBuffer(uid, uidLength)) {
        String cardID = bytes2hexStr(uid,uidLength);
        Serial.println("Valid Card: " +cardID);
        userLogin(cardID);

      }
      else{
        String cardID = bytes2hexStr(uid,uidLength);
        Serial.println("Invalid cardID: "+cardID);
        lcd.clear();
        lcd.print("Invalid Card");
        delay(1000);
        lcd.clear();
      }
    }

  }
  currentMillis = millis();
  if ((currentMillis - previousMillis >= interval) && queue_hasData()) {
     Serial.println("Processing Queue");
      previousMillis = currentMillis;
      processQueue();
  }



}



/* Interrupt Fuction for Button:
User can either Logoff or Report depending on state of the Appliance */
void button_pressed(){
  busy = true;
  delay(300);
  if (state){
    Serial.println("logoff");
    userLogoff();
  }
  else{
    Serial.println("report");
    userReport();
  }
  busy=false;
}


// Login User
void userLogin(String cardID){
  busy=true;
  lcd.clear();
  lcd.print("Logging In");

  state = true;
  EEPROM.write(511, 1);


  String req = ID;
  req+=",";
  req+=cardID;

  if ((processQueue() == 0) && (sendData(4,req) == 0)) {
  }
  else{
      Serial.println("data added to queue");
      queue_add(4,req);
  }

  String username = getUserName(cardID);

  Serial.print("Hello ");
  Serial.println(username);


  digitalWrite(onLed, HIGH);
  digitalWrite(offLed, LOW);
  digitalWrite(beepPin, HIGH);
  delay(130);
  digitalWrite(beepPin, LOW);
  lcd.clear();
  lcd.print("Logged in as: ");

  lcd.setCursor(0,1);
  lcd.print(username);
  busy=false;
}

// Report User
void userReport(){
  busy=true;
  lcd.clear();
  lcd.print("Reporting");

  if ((processQueue() == 0) && (sendData(5,ID)==0)){

  }
  else{
      Serial.println("data added to queue");
      queue_add(5,ID);
  }

  delay(1500);
  //lcd.clear();
  //lcd.print("Swipe card");
  busy=false;
}



// Logoff User
void userLogoff(){
  busy=true;
  lcd.clear();
  lcd.print("Logging Off");

  state = false;
  EEPROM.write(511, 0);


  if ((processQueue() == 0) && (sendData(3,ID) == 0)) {
  }
  else{
      Serial.println("data added to queue");
      queue_add(3,ID);
  }

  digitalWrite(onLed, LOW);
  digitalWrite(offLed, HIGH);
  digitalWrite(beepPin, HIGH);
  delay(130);
  digitalWrite(beepPin, LOW);
  lcd.clear();
  lcd.print("Swipe Card");
  busy=false;
}


String getUserName(String cardID){

  String resp;
  String req = "/appliances/getusername/";
  req+=cardID;
  req+=+"/";
  int t = httpRequest(req,resp);

  if (t != 0){
    return "User";
  }

  return resp;
}


// get application status from server
boolean getApplStatus(){

  String resp;
  String req = "/appliances/getappliancestatus/";
  req+=ID;
  req+=+"/";
  int t = httpRequest(req,resp);

  if (t != 0){
    return EEPROM.read(511);
  }


  if ((resp == "1") && (EEPROM.read(511)==1)){
    Serial.println("states match, device is on");
    return true;
  }
  else if ((resp == "0") && (EEPROM.read(511)==0)){

    Serial.println("states match, device is off");
    return false;
  }
  else{
    Serial.println("States dont match, loggin off");
    userLogoff();
  }


}


//get List of cards from server
void pollCardsFromServer() {

  Serial.println("Polling cards from server");
  String s;
  if (httpRequest("/hw/gcl", s) != 0) {
    return;
  }
  if (s.length() == 0) {
    return;
  }
  cardBuffer_reset();
  uint16_t start = 0;
  uint16_t en = 0;
  bool quit = false;
  do {
    en = s.indexOf(",", start);
    if ((en < 0) || (en == 65535)) {
      en = s.length();
      quit = true;
    }
    if ((en - start) % 2 != 0) {
      start = en + 1;
      continue;
    }
    uint8_t bLen = (en - start) / 2;
    uint8_t* b = new uint8_t[bLen];
    for (int i = 0; i < bLen; i++) {
      b[i] = hex2byte(s[start + 2 * i], s[start + 2 * i + 1]);
    }
    Serial.println(bytes2hexStr(b,bLen));
    cardBuffer_add(&b[0], bLen);
    start = en + 1;
    delete [] b;
  } while (!quit);

  // clean the rest of the buffer
  for (int i = cardBuffer_getCurrPos(); i <= CARDBUFFER_END; i++) {
    EEPROM.write(i, 0);
  }

}

/*Sends data to server or if offline puts into queue
cmd=3 -> Logoff
cmd=4 -> Login
cmd=5 -> Report
*/
uint8_t sendData(uint8_t cmd, String data) {
  String  url;
  url += "/hw/m/";
  url += ID;
  url += "/";
  if (cmd == 3) {
    url += encryptData("3," + data);
  } else if (cmd == 4) {
    url += encryptData("4," + data);
  } else if (cmd == 5) {
    url += encryptData("5," + data);
  } else {
    return 1;
  }

  String resp;
  if ( httpRequest(url, resp) != 0) {
    return 1;
  } else {
    Serial.println(resp);
    return 0;
  }
}

// sends get request and returns String inside '<' and '>' brackets
// returns 0 if all ok, 2 if timeout
uint8_t httpRequest(String url, String& response) {
  if (client.connect(server, HTTP_PORT)) {

    String request = "GET " + url + " HTTP/1.0";

    Serial.println(request);

    client.println(request);
    client.println();


    while (client.available() && (client.read() != '<')) {
    }
    char c;
    while (client.available() && ((c = client.read()) != '>')) {
      response += c;
    }
    client.stop();
    return 0;
  }
  else {
    client.stop();
    return 2;
  }
}



// ------------------- Card Buffer Code -------------------------
// for storing cardIDs in the EEPROM storage

uint16_t cardBuffer_getCurrPos() {
  uint16_t res = (EEPROM.read(CARDBUFFER_CURR_POS) << 8) | EEPROM.read(CARDBUFFER_CURR_POS + 1);
  return res;
}

uint8_t cardBuffer_setCurrPos(uint16_t newPosition) {
  if ((newPosition > CARDBUFFER_END) || (newPosition < CARDBUFFER_START)) {
    return 1;
  }
  else {
    uint8_t hByte = newPosition >> 8;
    uint8_t lByte = newPosition & 255;

    EEPROM.write(CARDBUFFER_CURR_POS, hByte);
    EEPROM.write(CARDBUFFER_CURR_POS + 1, lByte);

    return 0;
  }
}

uint16_t cardBuffPos = cardBuffer_getCurrPos();

/*  0 - ok
  1 - array length can't be 0
  2 - card is already in buffer
  3 - not enough space to write cardId    */
uint8_t cardBuffer_add(uint8_t* cardId, uint8_t idLength) {

  // check if cardId has valid length
  if (idLength == 0) {
    return 1;
  }

  // check if card already in buffer
  if (cardBuffer_isInBuffer(cardId, idLength)) {
    return 2;
  }

  // check if there is enough space in buffer to
  // write idLength + 1 bytes
  if ((cardBuffPos + idLength) > CARDBUFFER_END) {
    return 3;
  }

  EEPROM.write(cardBuffPos++, idLength);
  //cardBuffer_setCurrPos(cardBuffPos);
  for (int i = 0; i < idLength; i++) {
    EEPROM.write(cardBuffPos++, cardId[i]);
    //cardBuffer_setCurrPos(cardBuffPos);
  }
  cardBuffer_setCurrPos(cardBuffPos);
  return 0;
}
// check if card is in buffer
bool cardBuffer_isInBuffer(uint8_t* cardId, uint8_t idLength) {

  uint16_t pos = CARDBUFFER_START;
  bool isEqual;
  while (pos < cardBuffPos) {
    int len = EEPROM.read(pos++);
    if (len == 0) {
      return false;
    }
    if (len == idLength) {
      isEqual = true;
      for (int i = 0; i < idLength; i++) {
        //Serial.print(r);Serial.print(" is ");Serial.println(cardId[i]);
        if (EEPROM.read(pos + i) != cardId[i]) {
          isEqual = false;
          break;
        }
      }
    }
    if (isEqual) {
      return true;
    }
    pos += len;
  }
  return false;
}
// reset buffer
void cardBuffer_reset() {
  for (int i = CARDBUFFER_START; i <= CARDBUFFER_END; i++) {
    EEPROM.write(i, 0);
  }
  cardBuffPos = CARDBUFFER_START;
  cardBuffer_setCurrPos(cardBuffPos);
}

// -------------- QUEUE CODE ------------------------

uint16_t queue_getItemCount() {
  uint16_t res = (EEPROM.read(QUEUE_ITEM_COUNT) << 8) | EEPROM.read(QUEUE_ITEM_COUNT + 1);
  return res;
}

uint8_t queue_setItemCount(uint16_t value) {

  uint8_t hByte = value >> 8;
  uint8_t lByte = value & 255;

  EEPROM.write(QUEUE_ITEM_COUNT, hByte);
  EEPROM.write(QUEUE_ITEM_COUNT + 1, lByte);

  return 0;
}

uint16_t queue_getCursorStart() {
  uint16_t res = (EEPROM.read(QUEUE_CURSOR_START) << 8) | EEPROM.read(QUEUE_CURSOR_START + 1);
  if (res == 0) {
    res = QUEUE_START;
  }
  return res;
}

void queue_setCursorStart(uint16_t& value, uint16_t rShift) {

  value = (value - QUEUE_START + rShift) % (QUEUE_END - QUEUE_START + 1) + QUEUE_START;

  uint8_t hByte = value >> 8;
  uint8_t lByte = value & 255;

  EEPROM.write(QUEUE_CURSOR_START, hByte);
  EEPROM.write(QUEUE_CURSOR_START + 1, lByte);
}

uint16_t queue_getCursorEnd() {
  uint16_t res = (EEPROM.read(QUEUE_CURSOR_END) << 8) | EEPROM.read(QUEUE_CURSOR_END + 1);
  if (res == 0) {
    res = QUEUE_START;
  }
  return res;
}

uint8_t queue_setCursorEnd(uint16_t newPosition) {
  if ((newPosition > QUEUE_END) || (newPosition < QUEUE_START)) {
    return 1;
  }

  uint8_t hByte = newPosition >> 8;
  uint8_t lByte = newPosition & 255;

  EEPROM.write(QUEUE_CURSOR_END, hByte);
  EEPROM.write(QUEUE_CURSOR_END + 1, lByte);

  return 0;
}

uint16_t queue_inc_dataEnd() {
  uint16_t a = dataEnd;
  dataEnd = (dataEnd - QUEUE_START + 1) % (QUEUE_END - QUEUE_START + 1) + QUEUE_START;
  return a;
}

//returns current value of cursor and increases it by 1
uint16_t incCursor(uint16_t& cursorPtr) {
  uint16_t c = cursorPtr;
  cursorPtr = (cursorPtr - QUEUE_START + 1) % (QUEUE_END - QUEUE_START + 1) + QUEUE_START;
  return c;
}

// adds data to queue,
// command - represents action type
// data any string data that needed to be stored
uint8_t queue_add(uint8_t command, String data) {
  if (data.length() >= (QUEUE_END - QUEUE_START)) {
    return 1;
  }

  // keep removing data while queue is full or not enough space to put new data
  while (!queue_hasEnoughSpace(data.length() + 2)) {
    queue_remove();
  }

  int len = data.length();
  EEPROM.write(queue_inc_dataEnd(), len);
  EEPROM.write(queue_inc_dataEnd(), command);
  for (int i = 0; i < data.length(); i++) {
    EEPROM.write(queue_inc_dataEnd(), data[i]);
  }
  queue_setCursorEnd(dataEnd);
  queue_setItemCount(++itemCount);
  return 0;
}

// returns data that is first in queue
// but doesnt delete it
void queue_peek(uint8_t& command, String& data) {
  if (itemCount > 0) {
    uint16_t pos = dataStart;
    uint8_t len = EEPROM.read(incCursor(pos));
    command = EEPROM.read(incCursor(pos));
    for (int i = 0; i < len; i++) {
      data += (char) EEPROM.read(incCursor(pos));
    }
  }
}

// delete data that is first in queue
void queue_remove() {
  if (itemCount > 0) {
    uint8_t s = EEPROM.read(dataStart);
    // replace +2 with +1 if you don't use command option
    queue_setCursorStart(dataStart, s + 2);
    queue_setItemCount(--itemCount);
  }
}

bool queue_hasData() {
  return itemCount;
}

bool queue_hasEnoughSpace(uint8_t dataLen) {
  if (dataEnd > dataStart) {
    if (dataLen > (QUEUE_END - QUEUE_START + 1 - dataEnd + dataStart)) {
      return false;
    } else {
      return true;
    }
  } else if (dataStart > dataEnd) {
    if (dataLen > (dataStart - dataEnd)) {
      return false;
    } else {
      return true;
    }
  } else {
    if (itemCount > 0) {
      return false;
    } else {
      return true;
    }
  }
}

void queue_reset() {
  dataStart = QUEUE_START;
  queue_setCursorStart(dataStart, 0);
  dataEnd = QUEUE_START;
  queue_setCursorEnd(dataEnd);
  itemCount = 0;
  queue_setItemCount(itemCount);

  for (int i = QUEUE_START; i <= QUEUE_END; i++) {
    EEPROM.write(i, 0);
  }
}

//Processes actions stored in queue
uint8_t processQueue() {

  // process data in queue if exist any
  while (queue_hasData()) {
    String data;
    uint8_t cmd;
    queue_peek(cmd, data);
    if (sendData(cmd, data) != 0) {
      return 1;
    } else {
      queue_remove();
    }
  }
  return 0;
}

// ------------------------------------------------------------


// -------------- Encryption code -------------------

//Encrypts Data to be sent to Server
char* encryptData(String message){

  // get message length
  uint16_t len = message.length();

  // calculate cipher length, which is the least
  // value divisible by 16 and greater than len
  int ciLen = ((len- 1) / 16 + 1) * 16;

  // buff that holds 16 random bytes + cipher + 32 byte hash
  uint8_t buff[32 + ciLen];

  // convert String to byte array
  uint8_t bytes[ciLen];
  message.getBytes(bytes,len + 1);

  // set trailing bytes to zero
  memset(&bytes[len], 0, ciLen-len);

  // Serial.print("bytes: ");
  // Serial.println(bytes2hexStr(bytes,ciLen));

  // get one time pad from server
  String rnds;
  httpRequest("/hw/getotp/"+String(ID), rnds);
  Serial.print("OTP: "); Serial.println(rnds);
  uint8_t rnd[16];
  hex2byteArray(rnds,rnd);
  // getRndBytes(&buff[0]);

  // calculate the hash of rndBytes and device serial number
  Sha256.init();
  Sha256.write_L(rnd,16);
  Sha256.write_L(SN,16);
  uint8_t* hash = Sha256.result();

  AES128_encrypt(&buff[0], bytes, ciLen, &hash[16], &hash[0]);

  // calculate the hash of randBytes + password +
  // + encrypted message for message authentification
  Sha256.init();
  Sha256.write_L(rnd,16);
  Sha256.write_L(SN,16);
  Sha256.write_L(&buff[0],ciLen);
  memcpy(&buff[ciLen], Sha256.result(), 32);

  /* set up a destination buff large enough to hold the encoded data */
  char* output = (char*)malloc(((31 + ciLen) / 3 + 1) * 4 + 1);
  /* keep track of our encoded position */
  char* c = output;
  /* store the number of bytes encoded by a single call */
  int cnt = 0;
  /* we need an encoder state */
  base64_encodestate s;

  /*---------- START ENCODING ----------*/
  /* initialise the encoder state */
  base64_init_encodestate(&s);
  /* gather data from the input and send it to the output */
  cnt = base64_encode_block(buff, 32 + ciLen, c, &s);
  c += cnt;
  /* since we have encoded the entire input string, we know that
     there is no more input data; finalise the encoding */
  cnt = base64_encode_blockend(c, &s);
  c += cnt;
  *c = 0;
  /*---------- STOP ENCODING  ----------*/

  return output;
}

// check if server is a valid COLEMASS server
bool isServerValid() {
  uint8_t rndBytes[16];
  getRndBytes(rndBytes);
  String url = "/hw/c/";
  url += ID;
  url += "/";
  url += bytes2hexStr(rndBytes,16);
  String resp;

  if (httpRequest(url, resp) != 0){
    return false;
  }
  Serial.println(resp);
  if (resp.length() != 64) {
    return false;
  }
  uint8_t responseSha[32];

  // if response is not a valid hex string
  if (hex2byteArray(resp, responseSha) != 0) {
    return false;
  }
  Sha256.init();
  Sha256.write_L(rndBytes, 16);
  Sha256.write_L(SN, 16);
  uint8_t* challengeSha = Sha256.result();

  for (int i = 0; i < 32; i++) {
   // Serial.println(challengeSha[i]);
   // Serial.println(responseSha[i]);
    if (challengeSha[i] != responseSha[i]) {
      delete [] responseSha;
      delete [] challengeSha;
      return false;
    }
  }


  return true;
}

// generates 16 Random Bytes
void getRndBytes(uint8_t* buff){
  randomSeed(micros());
  for (int i = 0; i < 16; i++)
  {
    buff[i] = random(0,256);
  }
}

// ------------------------------------------------------

uint8_t hex2byte(char char1, char char2) {

  uint8_t a, b;
  if ((char1 >= '0') && (char1 <= '9')) {
    a = char1 - '0';
  } else if ((char1 >= 'A') && (char1 <= 'F')) {
    a = char1 - 'A' + 10;
  } else if ((char1 >= 'a') && (char1 <= 'f')) {
    a = char1 - 'a' + 10;
  }

  if ((char2 >= '0') && (char2 <= '9')) {
    b = char2 - '0';
  } else if ((char2 >= 'A') && (char2 <= 'F')) {
    b = char2 - 'A' + 10;
  } else if ((char2 >= 'a') && (char2 <= 'f')) {
    b = char2 - 'a' + 10;
  }

  return a * 16 + b;
}

uint8_t hex2byteArray(String hexStr, uint8_t* output) {

  uint16_t len = hexStr.length();
  if (len < 2) {
    return 1;
  }
  if ((len % 2) != 0) {
    return 1;
  }
  uint8_t a, b;
  char v1, v2;
  for (int i = 0; i < len / 2; i++) {
    v1 = hexStr[2 * i];
    v2 = hexStr[2 * i + 1];
    if ((v1 >= '0') && (v1 <= '9')) {
      a = v1 - '0';
    } else if ((v1 >= 'A') && (v1 <= 'F')) {
      a = v1 - 'A' + 10;
    } else if ((v1 >= 'a') && (v1 <= 'f')) {
      a = v1 - 'a' + 10;
    } else {
      return 2;
    }

    if ((v2 >= '0') && (v2 <= '9')) {
      b = v2 - '0';
    } else if ((v2 >= 'A') && (v2 <= 'F')) {
      b = v2 - 'A' + 10;
    } else if ((v2 >= 'a') && (v2 <= 'f')) {
      b = v2 - 'a' + 10;
    } else {
      return 2;
    }

    output[i] = a * 16 + b;
  }

  return 0;
}

String bytes2hexStr(uint8_t* bytes, int bytesLen) {
  int i;
  String output;
  for (i = 0; i < bytesLen; i++) {
    output += "0123456789abcdef"[bytes[i] >> 4];
    output += "0123456789abcdef"[bytes[i] & 0xf];
  }
  return output;
}
