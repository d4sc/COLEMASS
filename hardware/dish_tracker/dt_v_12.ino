#include <aes.h>
#include <sha256.h>
#include <sha256_config.h>
#include <cencode.h>
#include <EEPROM.h>
#include <Ethernet.h>
#include <string.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_PN532.h>

//serial number which acts as a password
#define SN (uint8_t*) "0123456789ABCDEF"
// hardware id
#define ID "disht"

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


// change this to the MAC printed on ethernet port on your board
byte mac[] = {0x98, 0x4F, 0xEE, 0x00, 0x2A, 0x9E};
IPAddress myIP(192, 168, 0, 202);
IPAddress server(192, 168, 0, 100);
EthernetClient client;

String dishTags[3]={"aa","ab","ac"};

int initLoc[3];
int postLoc[3];

// door settings
bool flip;
int irqpin = 3;
int ledpin = 13;
volatile int counter = 2;
volatile bool doorOpened = false;

// user card id
uint8_t uid[] = {0, 0, 0, 0, 0, 0, 0};

// nfc reader settings
#define PN532_IRQ   (2)
#define PN532_RESET (4)  // Not connected by default on the NFC Shield
Adafruit_PN532 nfc(PN532_IRQ, PN532_RESET);

// queue check interval
uint16_t queue_cc = 0;

// user cards check interval
uint16_t usrc_cc = 0;


uint16_t dataStart = queue_getCursorStart();
uint16_t dataEnd = queue_getCursorEnd();
uint16_t itemCount = queue_getItemCount();

void setup() {
  Serial.begin(115200);
  Serial.println();

  // start the Ethernet connection:
  Ethernet.begin(mac, myIP);

  // configure interrupt for logout button
  pinMode(irqpin, INPUT);
  pinMode(ledpin, OUTPUT);
  attachInterrupt(irqpin, buttonAction, CHANGE);

  // init nfc reader
  nfc.begin();
  if (!nfc.getFirmwareVersion()) {
    Serial.print("Didn't find PN53x board");
    while (1); // halt
  }
  nfc.setPassiveActivationRetries(80);
  nfc.SAMConfig();

  // download user cards from server
  if (isServerValid()){
    Serial.println("server is legit");
    pollCardsFromServer();
  } 

  // queue_reset();

  Serial.println("Ready.");
}

void loop() {
  boolean success;
  uint8_t uidLength;
  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, &uid[0], &uidLength);
  if (success) {

    Serial.println();

    // check if card is valid
    if (cardBuffer_isInBuffer(uid, uidLength)) {
      if (doorOpened) {
        Serial.println("Door is already opened.");
      } else {
        Serial.println("Door opened.");
        digitalWrite(ledpin, HIGH);
        doorOpened = true;
        initScan();
      }
    }
    Serial.println("");
    delay(500);
  }

  if (counter == 0) {
    if (doorOpened) {
      //close door and do stuff
      Serial.println("Door closed.");
      doorOpened = false;
      digitalWrite(ledpin, LOW);
      postScan();
      counter = 2;
    } else {
      Serial.println("Door is already closed.");
      counter = 2;
    }
  }

  queue_cc++;
  // usrc_cc++;

  // check once in 30 cycles (~15 sec) if there is any data in queue
  if ((queue_cc > 30) && queue_hasData() && !doorOpened) {
    queue_cc = 0;
    processQueue();
  }

  // poll cards from server once in 45 cycles (~22.5 sec)
  // if ((queue_cc > 45) && !doorOpened) {
  //   usrc_cc = 0;
  //   pollCardsFromServer();
  // }
}

// sends get request and returns String inside '<' and '>' brackets
// returns 0 if all ok, 2 if timeout
uint8_t httpRequest(String url, String& response) {
  if (client.connect(server, HTTP_PORT)) {

    String request = "GET " + url + " HTTP/1.0";
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

void buttonAction() {
  counter = ++counter % 2;
}

void initScan() {
  for (int i=0;i<3;i++){
    initLoc[i] = dLocation(analogRead(i));
    //Serial.println(initLoc[i]);
  }
}

void postScan() {
  for (int i=0;i<3;i++){
    postLoc[i] = dLocation(analogRead(i));
    //Serial.println(postLoc[i]);
  }

  String takeout;
  String putback;

  for (int i=0;i<3;i++){
    if ((initLoc[i]!=0)&&(postLoc[i]==0)){
      if (takeout.length()>0) {
        takeout+=",";
      }
      takeout+=dishTags[i];
    }
    if((initLoc[i]==0)&&(postLoc[i]!=0)){
      if (putback.length()>0) {
        putback+=",";        
      }
      putback+=dishTags[i];
    }
  }

  if (takeout.length()>0){
    Serial.print(takeout);Serial.println(" were taken out");
    takeout+=",";
    takeout += bytes2hexStr(uid,7);
    // Serial.print("Requesting ");
    // Serial.println(takeout);
    if (processQueue() == 0) {
      sendData(6,takeout);
    }
    else{
      Serial.println("data added to queue");
      queue_add(6,takeout);
    }
  }

  if (putback.length()>0){
    Serial.print(putback);Serial.println(" were put back");
    putback+=",";
    putback += bytes2hexStr(uid,7);
    // Serial.print("Requesting ");
    // Serial.println(putback);
    if (processQueue() == 0) {
      sendData(7,putback);
    }
    else{
      Serial.println("data added to queue");
      queue_add(7,putback);
    }
  }
}

uint8_t processQueue() {
  // process data in queue if exist any
  while (queue_hasData()) {
    // Serial.println("working on queue");
    // Serial.print("itemCount: ");Serial.println(itemCount);
    // Serial.print("dataStart: ");Serial.println(dataStart);
    // Serial.print("dataEnd: ");Serial.println(dataEnd);
    String data;
    uint8_t cmd;
    queue_peek(cmd, data);
    // Serial.print("peeked: ");Serial.print(cmd);Serial.print(",");Serial.println(data);
    if (sendData(cmd, data) != 0) {
      return 1;
    } else {
      queue_remove();
    }
  }
  return 0;
}

// 6- takeout, 7 - putback
uint8_t sendData(uint8_t cmd, String data) {
  String  url;
  url += "/hw/m/";
  url += ID;
  url += "/";
  if (cmd == 6) {
    // Serial.println("6," + data);
    url += encryptData("6," + data);
  } else if (cmd == 7) {
    // Serial.println("7," + data);
    url += encryptData("7," + data);
  } else {
    return 1;
  }

  String resp;
  if ( httpRequest(url, resp) != 0) {
    
    // Serial.print("adding to queue: ");Serial.print(cmd);Serial.print(",");Serial.println(data);
    // queue_add(cmd, data);
    return 1;
  } else {
    Serial.println(resp);
    return 0;
  }
}

uint8_t dLocation(int val) {
  if ((val >= 510)&&(val < 530)) return 1;
  if ((val >= 935)&&(val < 955)) return 2;
  return 0;
}

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


// ------------------- Card Buffer Code -------------------------

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
// command - represents action type, like 'putback' or 'takeout'
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

// -------------- Encryption code -------------------

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
  httpRequest("/hw/getotp/disht", rnds);
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
    if (challengeSha[i] != responseSha[i]) {
      delete [] responseSha;
      delete [] challengeSha;
      return false;
    }
  }
  return true;
}

void getRndBytes(uint8_t* buff){
  randomSeed(micros());
  for (int i = 0; i < 16; i++)
  {
    buff[i] = random(0,256);
  }
}
