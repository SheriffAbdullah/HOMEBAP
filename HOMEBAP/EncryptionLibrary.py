import hashlib

def OneWayHashed(text):
    '''
    The hashlib.sha256() method creates a SHA-256 hash object, 
    which can then be used to hash the input string using the 
    hexdigest() method. 
    
    The encode() method is used to convert the input string to 
    bytes, which is required by the hashlib module.

    Note that this method only generates a one-way hash, which 
    cannot be reversed to obtain the original input string. It 
    is often used to store passwords in a database, where the 
    hashed value can be compared to a newly hashed version of 
    a user-entered password to authenticate the user.
    
    Also note, the SHA-256 algorithm generates a 64-character 
    hash string.
    '''
    
    hash_object = hashlib.sha256(text.encode())
    return hash_object.hexdigest()

def Salted(text, key):
    '''
    Salting is a technique to protect passwords stored in 
    databases by adding a string of characters 
    and then hashing them.
    
    E.g.    
    text = "randomtext" & key = 4
    Salted(text, key) will return "r4a4n4d4o4m4t4e4x4t4"
    '''
    
    salted = ""
    letters = list(text)
    
    for letter in letters:
        salted += letter + str(key)
        
    return salted

