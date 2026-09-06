const users = [
  {
    email: 'admin55@gmail.com',
    passwordHash: '2809c9ba986a16f90c6d9cc2d5d45f9fbb62ab1aeec8132d0570735333d9a5e4',
    name: 'Admin',
    role: 'admin'
  }
];

export function findUserByEmail(email) {
  return users.find(u => u.email === email);
}
