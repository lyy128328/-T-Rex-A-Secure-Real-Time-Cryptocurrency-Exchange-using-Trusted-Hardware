#include "Enclave1_t.h"

#include "sgx_trts.h"
#include <string.h>
#include <stdio.h>
#include <cstring>
#include <cstdlib>
#include <iostream>

#include "sgx_tcrypto.h"
sgx_ecc_state_handle_t ctx;
sgx_ec256_private_t p_private;
sgx_ec256_public_t p_public;

void foo(unsigned char* message, size_t msg_len, char *buf, size_t buf_len)
{
	/*
	const char *secret = "Hello Enclave!";
	if (buf_len > msg_len)
	{
		memcpy(buf, message, msg_len + 1);
	}
	*/


	int function_status = -1;
	//EC_KEY *eckey = EC_KEY_new();
	//ECDSA_SIG *signature;
	/*
	if (NULL == eckey)
	{
		//printf("Failed to create new EC Key\n");
		function_status = -1;
	}
	else
	{
		EC_GROUP *ecgroup = EC_GROUP_new_by_curve_name(NID_secp256k1);
		if (NULL == ecgroup)
		{
			//printf("Failed to create new EC Group\n");
			function_status = -1;
		}
		else
		{
			int set_group_status = EC_KEY_set_group(eckey, ecgroup);
			const int set_group_success = 1;
			if (set_group_success != set_group_status)
			{
				//printf("Failed to set group for EC Key\n");
				function_status = -1;
			}
			else
			{
				const int gen_success = 1;
				int gen_status = EC_KEY_generate_key(eckey);
				if (gen_success != gen_status)
				{
					//printf("Failed to generate EC Key\n");
					function_status = -1;
				}
				else
				{
					EC_GROUP *ecgroup = EC_GROUP_new_by_curve_name(NID_secp256k1);
					if (NULL == ecgroup)
					{
						//printf("Failed to create new EC Group\n");
						function_status = -1;
					}
					else
					{
						int set_group_status = EC_KEY_set_group(eckey, ecgroup);
						const int set_group_success = 1;
						if (set_group_success != set_group_status)
						{
							//printf("Failed to set group for EC Key\n");
							function_status = -1;
						}
						else
						{
							const int gen_success = 1;
							int gen_status = EC_KEY_generate_key(eckey);
							if (gen_success != gen_status)
							{
								//printf("Failed to generate EC Key\n");
								function_status = -1;
							}
							else
							{
								signature = ECDSA_do_sign(message, strlen((char*)message), eckey);
								//std::cout << signature->r << " " << signature->s << endl;
								if (NULL == signature)
								{
									//printf("Failed to generate EC Signature\n");
									function_status = -1;
								}
								else
								{

									int verify_status = ECDSA_do_verify(message, strlen((char*)message), signature, eckey);
									const int verify_success = 1;
									if (verify_success != verify_status)
									{
										//printf("Failed to verify EC Signature\n");
										function_status = -1;
									}
									else
									{
										//printf("Verifed EC Signature\n");
										function_status = 1;
									}
								}
							}
						}
						EC_GROUP_free(ecgroup);
					}
					EC_KEY_free(eckey);
				}
			}
		}
	}
	*/
		
		//char* r_str = BN_bn2hex(signature->r);
		//memcpy(buf, r_str, strlen(r_str) + 1);
}

int init()
{
	
	sgx_status_t ret = SGX_SUCCESS;
	ret = sgx_ecc256_open_context(&ctx);
	if (ret != SGX_SUCCESS)
		return ret;
	ret = sgx_ecc256_create_key_pair(&p_private, &p_public, ctx);
	
	return ret;
}


int sign(char* message, size_t len, char* buff, size_t sig_len)
{
	
	
	//if (sig_len != sizeof(sgx_ec256_signature_t))
		//return -1;
	sgx_ec256_signature_t sig;

	sgx_status_t ret = sgx_ecdsa_sign((uint8_t*)message, len, &p_private, (sgx_ec256_signature_t*)&sig, ctx);
	memcpy(buff, sig.x, sizeof(sig.x));

	return ret;
}

/*
int sign(unsigned char* message, size_t len, void* buff, size_t sig_len)
{
int function_status = -1;
EC_KEY *eckey = EC_KEY_new();
if (NULL == eckey)
{
//printf("Failed to create new EC Key\n");
function_status = -1;
}
else
{
EC_GROUP *ecgroup = EC_GROUP_new_by_curve_name(NID_secp256k1);
if (NULL == ecgroup)
{
//printf("Failed to create new EC Group\n");
function_status = -1;
}
else
{
int set_group_status = EC_KEY_set_group(eckey, ecgroup);
const int set_group_success = 1;
if (set_group_success != set_group_status)
{
//printf("Failed to set group for EC Key\n");
function_status = -1;
}
else
{
const int gen_success = 1;
int gen_status = EC_KEY_generate_key(eckey);
if (gen_success != gen_status)
{
//printf("Failed to generate EC Key\n");
function_status = -1;
}
else
{
buff = ECDSA_do_sign(message, strlen((char*)message), eckey);
if (NULL == buff)
{
//printf("Failed to generate EC Signature\n");
function_status = -1;
}
else
{

int verify_status = ECDSA_do_verify(message, strlen((char*)message), (ECDSA_SIG*)buff, eckey);
const int verify_success = 1;
if (verify_success != verify_status)
{
//printf("Failed to verify EC Signature\n");
function_status = -1;
}
else
{
//printf("Verifed EC Signature\n");
function_status = 1;
}
}
}
}
EC_GROUP_free(ecgroup);
}
EC_KEY_free(eckey);
}

return function_status;
}
*/
int verify(char* message, size_t len, void* buff, size_t sig_len)
{
	uint8_t res;

	if (sig_len != sizeof(sgx_ec256_signature_t))
		return -1;

	sgx_status_t ret = sgx_ecdsa_verify((uint8_t*)message, len, &p_public, (sgx_ec256_signature_t*)buff, &res, ctx);

	return res;

}

int close()
{
	return sgx_ecc256_close_context(&ctx);
}
