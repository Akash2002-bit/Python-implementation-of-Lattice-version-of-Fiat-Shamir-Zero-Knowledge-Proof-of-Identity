
import hashlib
import random
import math


# 32 byte array generator
def generate_random_array():
    return [random.randint(0, 255) for _ in range(32)]

# Algorithm 3
def BitsToBytes(b):
    B = [0] * (len(b) // 8)
    
    for i in range(len(b)):
        B[i // 8] += b[i] * (2 ** (i % 8))
    return B 

# Algorithm 4    
def BytesToBits(B):
    b = [0] * (8 * len(B))   
    C = B.copy() 
      
    for i in range(len(B)):
        for j in range(8):
            b[8 * i + j] = C[i] % 2 
            C[i] = math.floor(C[i]/2)
    return b

# Bit reversal of seven-bit integer
def reverse_bits_7bit(r):
    if r < 0 or r > 127:
        raise ValueError("Input must be a 7-bit integer (0 to 127).")
    binary_str = f'{r:07b}'
    reversed_binary_str = binary_str[::-1]
    return int(reversed_binary_str, 2)

# Compression
def compress(ZQ, d):
    Z2D = [0]*(len(ZQ))
    
    for i in range(len(ZQ)):
        Z2D[i] = (round_nearest(((2**d) / q) * ZQ[i])) % (2**d)
    
    return Z2D

# Decompression
def decompress(Z2D, d):
    ZQ = [0] * len(Z2D)
    for i in range(len(Z2D)):
        ZQ[i] = round_nearest(((q/(2**d)) * Z2D[i]))
    
    return ZQ

# Algorithm 5
def ByteEncode(F, d):
    b = [0] * (256 * d)
    
    for i in range(256):
        a = F[i] 
        for j in range(d):
            b[i * d + j] = a % 2
            a = (a - b[i * d + j]) // 2
    B = BitsToBytes(b)   
    return B

# Algorithm 6
def ByteDecode(B, d):
    b = BytesToBits(B)
    F = [0] * 256
    m = 2**d if d < 12 else 3329

    for i in range(256):
        for j in range(d):
            F[i] += (b[i * d + j] * (2 ** j)%m)%m
        F[i] = F[i] % m    
    
    return F

# SHAKE128 initialization
def XOF_Init():
    return hashlib.shake_128()

# Absorb input byte array into the XOF context
def XOF_Absorb(ctx, B):
    # Absorb the byte array as is (B is already a byte array)
    return ctx.update(B) 

# Squeeze out length bytes from the XOF context
def XOF_Squeeze(ctx, length: int) -> bytes:
    # Squeeze out 8 * length bytes
    return ctx.digest(8 * length)

#def H_hash(x):
#    input_bytes = bytes(x)
#    sha3_hash = hashlib.sha3_256(input_bytes).digest()
#    y = list(sha3_hash[:32])
#    return y

def H_hash(x):
    # Convert input to bytes if not already in byte format
    if isinstance(x, (list, tuple)):
        # Normalize values to fit within byte range (0-255) using modulo or custom encoding
        input_bytes = bytes([val % 256 for val in x])
    elif isinstance(x, int):
        # For a single integer, convert to bytes representation
        input_bytes = x.to_bytes((x.bit_length() + 7) // 8, byteorder='big')
    else:
        # Assume x is already in bytes if none of the above types
        input_bytes = bytes(x)

    sha3_hash = hashlib.sha3_256(input_bytes).digest()
    y = list(sha3_hash[:32])
    return y

# Algorithm 7
def SampleNTT(B):   
    B = bytes(B[:])

    ctx = XOF_Init()   
    XOF_Absorb(ctx, B)  
    samples = [0] * 256  
    j = 0

    while j < 256:
        C = XOF_Squeeze(ctx, 3)  # Fresh 3-byte array C from XOF
        d1 = C[0] + 256 * (C[1] % 16)   # 0 <= d1 < 2^12
        d2 = (C[1] // 16) + 16 * C[2]   # 0 <= d2 < 2^12

        if d1 < q:
            samples[j] = d1
            j += 1

        if d2 < q and j < 256:
            samples[j] = d2
            j += 1

        if j < 256:  # Avoid unnecessary squeeze if we've reached the sample limit
            ctx.update(C) 
            
    return list(samples)

# Algorithm 8
def SamplePolyCBD(B, eta):
    b = BytesToBits(B)
    f = [0]*256
    for i in range(256):
        x = sum(b[2*i*eta + j] for j in range(eta)) 
        y = sum(b[2*i*eta + eta + j] for j in range(eta)) 
        f[i] = (x - y) % q 

    return f

# Algorithm 9
def NTT(f):
    n = len(f) 
    f_hat = f[:] # Copy the input array to avoid modifying it in place
    i = 1
    length = 128
    while length >= 2:
        for start in range(0, n, 2 * length):
            zeta = pow(17, reverse_bits_7bit(i)) % q
            i += 1
            for j in range(start, start + length):
                t = (zeta * f_hat[j + length]) % q
                f_hat[j + length] = (f_hat[j] - t) % q
                f_hat[j] = (f_hat[j] + t) % q
        length //= 2
    return f_hat

# Algorithm 10
def NTTinverse(f_hat):
    f = f_hat[:] 
    n = len(f) 
    i = 127 
    
    length = 2
    while length <= 128:
        for start in range(0, n, 2 * length):
            zeta = pow(17, reverse_bits_7bit(i))%q 
            i -= 1  
            for j in range(start, start + length):
                t = f[j]
                f[j] = (t + f[j + length]) % q 
                f[j + length] = (zeta * (f[j + length] - t)) % q
        length *= 2 

    f = [(val * 3303) % q for val in f]   
    
    return f

# Algorithm 11
def MultiplyNTTs(f_hat, g_hat):
    h_hat = [0] * 256
    
    for i in range(128):
        a0, a1 = f_hat[2 * i], f_hat[2 * i + 1]
        b0, b1 = g_hat[2 * i], g_hat[2 * i + 1]
        gamma = pow(17, 2*reverse_bits_7bit(i) + 1)

        h_hat[2 * i], h_hat[2 * i + 1] = BaseCaseMultiply(a0, a1, b0, b1, gamma)
    
    return h_hat

# Algorithm 12
def BaseCaseMultiply(a0, a1, b0, b1, gamma):
    c0 = (a0 * b0 + a1 * b1 * gamma) % q
    c1 = (a0 * b1 + a1 * b0) % q
    return c0, c1 

def custom_add(list1, list2):
    result = [0] * 256
    for i in range(256):
        result[i] = (list1[i] + list2[i])%q  # Element-wise addition
    
    return result 

def custom_sub(list1, list2):
    result = [0] * 256
    for i in range(256):
        result[i] = (list1[i] - list2[i])%q  # Element-wise addition
    
    return result


def PRF(array1, eta):
    # Concatenate the two arrays
    concatenated_input = bytes(array1)
    output_length = 64 * eta
    # Use SHAKE256 with the concatenated input and desired output length
    shake = hashlib.shake_256()
    shake.update(concatenated_input)
    shake_output = shake.digest(output_length)
    output_array = [int(byte) for byte in shake_output]
    
    return output_array

def round_nearest(n):
    # Get the fractional part of the number
    fractional_part = n - int(n)    
    # Check if the number is of the form n + 0.5
    if fractional_part == 0.5:
        return int(n) + 1  # Round up to n + 1
    else:
        return round(n)
    
def string_to_ascii_list(input_string):
    return [ord(char) for char in input_string]    
  
def peggy(err1_seed, err2_seed, A_seed, c_seed):
    c_hat = NTT(SamplePolyCBD(PRF(c_seed, eta1), eta1))
    c = NTTinverse(c_hat)
    #print(c)
    
    k = H_hash(string_to_ascii_list(secret) + string_to_ascii_list(salt))
    x_hat = SampleNTT(k)
    #print("xhat", x_hat)
    x = NTTinverse(x_hat)
    
    e1 = (SamplePolyCBD(PRF(err1_seed, eta1), eta1))
    e2 = (SamplePolyCBD(PRF(err2_seed, eta1), eta1))
    
    A_hat = SampleNTT(A_seed)
    A = NTTinverse(A_hat)
    
    B = custom_add(NTTinverse(MultiplyNTTs(A_hat, x_hat)), e1)
    
    v_seed = generate_random_array()
    v_hat = SampleNTT(v_seed)
    v = NTTinverse(v_hat)
    
    r = custom_sub(v, NTTinverse(MultiplyNTTs(x_hat, c_hat)))
    Z = custom_add(NTTinverse(MultiplyNTTs(A_hat, v_hat)), e2)
    
    return B, r, Z, c, A
    

     
def victor(B, r, Z, c, A):
    rA = NTTinverse(MultiplyNTTs(NTT(r), NTT(A)))
    #print("rA: ", rA)
    proof1 = compress(rA, 1)
    print("proof1: ", proof1)
    
    
    ZcB = custom_sub(Z, NTTinverse(MultiplyNTTs(NTT(c), NTT(B))))
    #print("ZcB: ", ZcB)
    proof2 = compress(ZcB, 1)
    print("proof2: ", proof2)
    
    differences = 0
    for i in range(len(proof1)):
        if proof1[i] != proof2[i]:
            differences += 1
    
    return differences

                          

n = 256
q = 3329

eta1 = 3

c_seed = generate_random_array() #challenge from victor

err1_seed = generate_random_array() #error bytes seed
err2_seed = generate_random_array()
A_seed = generate_random_array()

secret = "password"
salt = "salt"


B, r, Z, c, A = peggy(err1_seed, err2_seed, A_seed, c_seed)

TF = victor(B, r, Z, c, A)
print(TF)

