import colorsys
import numpy as np


class HSLDiscreteColorGenerator:
    
    def __init__(self, H, S=1, L=.5, mode='all', order='lsh', hshift=0, loophshift=False):
        self.H, self.S, self.L = self.parse_hsv(H, S, L)
        self.mode = mode 
        self.order = order
        self.hshift = hshift
        self.loophshift = loophshift
        
    def parse_hsv(self, H, S, L):
        """parse input HSL color settings"""
        if isinstance(H, np.ndarray):
            pass
        elif isinstance(H, float) or H == 1:
            H = np.array([H], dtype=float)
        elif isinstance(H, int):
            H = np.linspace(0, 1, H+1)[1:]
            
        if isinstance(S, np.ndarray):
            pass
        elif isinstance(S, float) or S == 1:
            S = np.array([S], dtype=float)
        elif isinstance(S, int):
            S = np.linspace(0, 1, S+1)[1:][::-1]
            
        if isinstance(L, np.ndarray):
            pass
        elif isinstance(L, float) or L == 1:
            L = np.array([L], dtype=float)
        elif isinstance(L, int):
            L = np.linspace(0, 1, L+2)[1:-1][::-1]
            
        return H, S, L
        
    def combine(self, force_on_overflow=False):
        """combine HSL colors together"""
        if self.mode == 'all':
            if not force_on_overflow and self.H.size*self.S.size*self.L.size > 1000:
                raise ValueError('too many colors')
            H, S, L = map(self.flatten, np.meshgrid(self.H, self.S, self.L, indexing='ij'))
        elif self.mode == 'map':
            H, S, L = self.map_hsv(self.H, self.S, self.L)
        
        return np.array([H, S, L], dtype=float).T
    
    def map_hsv(self, H, S, L):
        """map hsl values of same size or size 1 together"""
        size = max([v.size for v in (H, S, L)])
        if H.size == 1:
            H = np.repeat(H, size)
        elif H.size != size:
            raise ValueError('cannot map HSV of unequal size')
            
        if S.size == 1:
            S = np.repeat(S, size)
        elif S.size != size:
            raise ValueError('cannot map HSV of unequal size')
            
        if L.size == 1:
            L = np.repeat(L, size)
        elif L.size != size:
            raise ValueError('cannot map HSV of unequal size')
            
        return H, S, L
        
    def flatten(self, data):
        """flatten dimensions based on specified order"""
        data = np.swapaxes(data, 'hsl'.index(self.order[0]), 2)
        data = np.swapaxes(data, 'hsl'.index(self.order[1]), 1)
        return data.flatten()
        
    def generate(self, N=None, force_on_overflow=False):
        """generate colors"""
        HSL = self.combine(force_on_overflow=force_on_overflow)
        colors = []
        for h, s, l in HSL:
            h = (h+self.hshift) % 1.
            colors.append(colorsys.hls_to_rgb(h, l, s))
            
            if N is not None and len(colors) >= N:
                break
                
        return np.array(colors)
    
    
def generate_discrete_hsl(H, S=1, L=.5, mode='all', order='lsh', hshift=0, loophshift=False, N=None):
    return HSLDiscreteColorGenerator(H=H, S=S, L=L, mode=mode, order=order, hshift=hshift, loophshift=loophshift).generate(N=N)
