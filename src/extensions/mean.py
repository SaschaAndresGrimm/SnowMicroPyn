import matplotlib.pyplot as plt
import numpy as np

class Drift(object):
    def __init__(self,x,y):
        self.dataX = x
        self.dataY = y   
        
        self.fig, (self.ax, self.ax2) = plt.subplots(2, 1)
        self.fig.canvas.set_window_title('SMP Mean Value, Drift and Noise Analysis Tool') 
        
        self.fig.subplots_adjust(hspace=0.4 )
        
        self.clicks = 0
        self.mouseState = False
        
        self.v1  = self.ax.axvline(x = x[0], color = "red", visible = False, linewidth=3, alpha=0.6)
        self.v2 = self.ax.axvline(x = x[-1], color = "red", visible = False, linewidth=3, alpha=0.6)

        self.ax.set_title('Original Data')
        self.ax.set_xlabel("Depth [mm]")
        self.ax.set_ylabel("Force [N]")
        self.ax2.set_title("Selected Range")
        self.ax2.set_ylabel("Force [N]")
        self.ax2.set_xlabel("Depth [mm]")
        self.line, = self.ax.plot(self.dataX, self.dataY, picker=5)  # 5 points tolerance
        
        self.fig.canvas.mpl_connect('pick_event', self.onPick)
        self.fig.canvas.mpl_connect('button_press_event', self.mouseDown)
        self.fig.canvas.mpl_connect('motion_notify_event', self.mouseMotion)
        self.fig.canvas.mpl_connect('button_release_event', self.mouseUp)
        
        plt.show()
     
    def mouseDown(self, event):
        if self.v1 in self.fig.hitlist(event) or self.v2 in self.fig.hitlist(event):
            self.mouseState = True
    
    def mouseMotion(self, event):
        if self.mouseState:
            x, y = event.xdata, event.ydata
            if x is None or y is None:
                self.picked = None
                return
            
            if self.v1 in self.fig.hitlist(event):
                self.picked = "v1"
            
            if self.v2 in self.fig.hitlist(event):
                self.picked = "v2"
            
            self.update(event)
            
    def mouseUp(self, event):
        self.mouseState = False
        self.picked = None
        
    def onPick(self,event):
        self.clicks += 1

        x = event.mouseevent.xdata
        y = event.mouseevent.ydata
        
        distances = np.hypot(x-self.dataX[event.ind], y-self.dataY[event.ind])
        indmin = distances.argmin()
        self.index = event.ind[indmin]
        self.update(event)
        
    def update(self, event):

        if self.index is None: return
    
        if self.clicks == 1:
            v = ([self.dataX[self.index],self.dataX[self.index]],[0,10])
            self.v1.set_data(v)
            self.v1.set_visible(True)
            
        if self.clicks == 2:
            self.clicks += 1
            v = ([self.dataX[self.index],self.dataX[self.index]],[0,10]) 
            self.v2.set_data(v) 
            self.v2.set_visible(True)
            
        if self.clicks >= 2:
            
            self.ax2.clear()
            self.ax2.set_title("Selected Range")
            self.ax2.set_ylabel("Force [N]")
            self.ax2.set_xlabel("Depth [mm]")
            
            if self.mouseState:
                x = event.xdata
                v = ([x,x],[0,10])
                if self.picked == "v1":
                    self.v1.set_data(v)
                if self.picked == "v2":
                    self.v2.set_data(v)
                
            args = [self.v1.get_data()[0][0],self.v2.get_data()[0][0]] 
            
            min = np.where(self.dataX >= np.amin(args))[0][0]
            max = np.where(self.dataX >= np.amax(args))[0][0]
            
            x = self.dataX[min:max]
            y = self.dataY[min:max]
            
            self.ax2.plot(x,y)
            self.ax2.set_xlim((np.amin(x),np.amax(x)))
            self.ax2.set_title("Selected Range")
            self.ax2.set_ylim((np.amin(y),2*np.amax(y)))
            
            self.linFit(x,y)
            
        self.fig.canvas.draw()
        
    def linFit(self,x,y):
        mean = np.mean(y)
        dev = np.std(y)
        m,c = np.polyfit(x, y, 1)
        y_fit = x*m+c
        std = np.sqrt(np.mean((y-y_fit)**2))
        self.ax2.plot(x,y_fit, "r--",x,y_fit+std, "b:",x,y_fit-std,"b:")
        self.ax2.text(0.05, 0.9, 'Mean: (%.2e +- %.2e) N\nSlope: %.2e N/m\nStd: %.2e N' %(mean, dev, m*1000, std), transform=self.ax2.transAxes, va='top')        

if __name__ == "__main__":
    test = Drift(np.arange(0,10000), np.random.normal(0,1,10000))