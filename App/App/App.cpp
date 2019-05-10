// App.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"
#include <iostream>
using namespace std;

#include <stdio.h>
#include <tchar.h>
#include "sgx_urts.h"
#include "Enclave1_u.h"
#define ENCLAVE_FILE _T("enclave1.signed.dll")
#define MAX_BUF_LEN 1024 
#include "sgx_tcrypto.h"

#include <openssl/ec.h>      // for EC_GROUP_new_by_curve_name, EC_GROUP_free, EC_KEY_new, EC_KEY_set_group, EC_KEY_generate_key, EC_KEY_free
#include <openssl/ecdsa.h>   // for ECDSA_do_sign, ECDSA_do_verify
#include <openssl/obj_mac.h> // for NID_secp192k1
#include <openssl/bn.h>

#pragma comment (lib, "Ws2_32.lib")
#pragma comment (lib, "Mswsock.lib")
#pragma comment (lib, "AdvApi32.lib")

int main()
{
	WSADATA WSAData;

	SOCKET server, client;

	SOCKADDR_IN serverAddr, clientAddr;

	WSAStartup(MAKEWORD(2, 0), &WSAData);
	server = socket(AF_INET, SOCK_STREAM, 0);
	serverAddr.sin_addr.s_addr = INADDR_ANY;
	serverAddr.sin_family = AF_INET;
	serverAddr.sin_port = htons(5537);

	bind(server, (SOCKADDR *)&serverAddr, sizeof(serverAddr));
	listen(server, 0);

	cout << "Listening for incoming connections..." << endl;

	char message[MAX_BUF_LEN];
	int clientAddrSize = sizeof(clientAddr);

	sgx_enclave_id_t eid;
	sgx_status_t ret = SGX_SUCCESS;
	sgx_launch_token_t token = { 0 };
	int updated = 0;
	char buffer[MAX_BUF_LEN] = "Hello World!";

	
	// Create the Enclave with above launch token.
	ret = sgx_create_enclave(ENCLAVE_FILE, SGX_DEBUG_FLAG,
		&token, &updated,
		&eid, NULL);
	if (ret != SGX_SUCCESS) {
		printf("App: error %#x, failed to create enclave.\n",
			ret);
		return -1;
	}


	int res = -1;
	ret = init(eid, &res);
	
	//printf("%s", buffer);
	cout << "In Enclave" << endl;
	while (1) {
		//cout << "In while" << endl;
		if ((client = accept(server, (SOCKADDR *)&clientAddr, &clientAddrSize)) != INVALID_SOCKET)
		{
			memset(message, 0, sizeof(message));
			//cout << "Client connected!" << endl;
			recv(client, (char*)message, sizeof(buffer), 0);
			//cout << "Client says: " << message << endl;
			// A bunch of Enclave calls (ECALL) will happen here.

			ret = sign(eid, &res, message, strlen((char*)message), buffer, MAX_BUF_LEN);
			
			//foo(eid, message, strlen((char*)message), buffer, MAX_BUF_LEN);
			
			char sig_x[64];
			for (int i = 0; i < 32; i++) {
				int dec = abs(buffer[i]);
				int quotient = dec / 16;
				int remainder = dec % 16;
				char result1;
				if (quotient < 10) {
					result1 = '0' + quotient;
				}
				else {
					result1 = (char)(55 + quotient);
				}
				char result2;
				if (remainder< 10) {
					result2 = '0' + remainder;
				}
				else {
					result2 = (char)(55 + remainder);
				}
				sig_x[i * 2] = result1;
				sig_x[i * 2 + 1] = result2;
			}
			//for (int i = 0; i < 64; i++) {
				//printf("%c", sig_x[i]);
			//}
			//printf("\n");
			int isSendResult = send(client, sig_x, 64, 0);
			
		}

		closesocket(client);
		//cout << "\nClient disconnected." << endl;
	}
	
	// Destroy the enclave when all Enclave calls finished.
	if (SGX_SUCCESS != sgx_destroy_enclave(eid))
		return -1;
	cin.get();
}

