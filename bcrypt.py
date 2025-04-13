import bcrypt

# Password to hash
password = b"admin123"

# Generate salt
salt = bcrypt.gensalt()

# Generate hash
hashed = bcrypt.hashpw(password, salt)

# Print the result
print(hashed.decode())
