
class Auth {
    constructor() {
        this.baseUrl = '/api';
        this.token = localStorage.getItem('token');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
    }

    async signup(userData) {
        try {
            console.log('Sending signup data:', userData);

            const response = await fetch(`${this.baseUrl}/auth/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();
            console.log('Signup response:', data);

            if (response.ok) {
                if (data.token) {
                    this.setToken(data.token);
                    this.setUser(data.user);
                    return { success: true, data };
                } else {
                    return { success: false, message: 'No token received' };
                }
            } else {
                return { success: false, message: data.message || 'Signup failed' };
            }
        } catch (error) {
            console.error('Signup error:', error);
            return { success: false, message: 'Network error. Please check if backend is running.' };
        }
    }

    async signin(credentials) {
        try {
            console.log('Sending signin data:', credentials);

            const response = await fetch(`${this.baseUrl}/auth/signin`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(credentials)
            });

            const data = await response.json();
            console.log('Signin response:', data);

            if (response.ok) {
                if (data.token) {
                    this.setToken(data.token);
                    this.setUser(data.user);
                    return { success: true, data };
                } else {
                    return { success: false, message: 'No token received' };
                }
            } else {
                return { success: false, message: data.message || 'Login failed' };
            }
        } catch (error) {
            console.error('Signin error:', error);
            return { success: false, message: 'Network error. Please check if backend is running.' };
        }
    }

    async googleSignin(credential) {
        try {
            console.log('Sending Google credential to backend...');

            const response = await fetch(`${this.baseUrl}/auth/google`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ credential })
            });

            const data = await response.json();

            if (response.ok) {
                if (data.token) {
                    this.setToken(data.token);
                    this.setUser(data.user);
                    return { success: true, data };
                } else {
                    return { success: false, message: 'No token received from backend' };
                }
            } else {
                return { success: false, message: data.message || 'Google Login failed' };
            }
        } catch (error) {
            console.error('Google Signin error:', error);
            return { success: false, message: 'Network error. Please check if backend is running.' };
        }
    }

    async verifyToken() {
        if (!this.token) return false;

        try {
            const response = await fetch(`${this.baseUrl}/auth/verify`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                if (data.user) {
                    this.setUser(data.user);
                }
                return true;
            }
            return false;
        } catch (error) {
            console.error('Verify error:', error);
            return false;
        }
    }

    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        this.token = null;
        this.user = null;
        window.location.href = '/';
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('token', token);
    }

    setUser(user) {
        this.user = user;
        localStorage.setItem('user', JSON.stringify(user));
    }

    isAuthenticated() {
        return !!this.token;
    }

    getUser() {
        return this.user;
    }

    getAuthHeader() {
        return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
    }
}

window.auth = new Auth();