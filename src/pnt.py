"""
pnt.py contains the Pnt object to parse, manipulate, and save
binary SnowMicroPen measurement .pnt files.

Contact: sascha.grimm@dectris.com, loewe@slf.ch

example:

import pnt
import matplotlib.pylab as plt

p = pnt.Pnt("/path/to/file.pnt", verbose=True) # open a .pnt file, set verbosity

print p.header # print meta data dict
p.writeHeader("header.txt") # write header data as txt file

plt.plot(p.data[:,0], p.data[:,1]); plt.show() # plot force displacement curve

p.fromFile("other/filename.pnt") # load new file into object p

p.header["Comment"] = "custom comment" # modify meta data "Comment"
p.writePnt() # write modified meta data to .pnt file
"""

import struct
import os
import numpy

__author__ = "SasG"
__date__ = "16/03/28"
__version__ = "0.1.0"

#.pnt structure parameter table containing:
# [parameter name, binary type, start bit, bit length, physical unit]
PARAMTABLE = [["Version","H",0,2, None], # .pnt file version
			["Tot Samples","i",2,4, None], # number of samples ??? maybe num of force samples + number of t samples ???
			["Samples Dist [mm]","f",6,4, "mm"], # displacement betweene consecutive force samples
			["CNV Force [N/mV]","f",10,4, "N/mV"], # force conversion factor
			["CNV Pressure [N/bar]","f",14,4, "N/bar"], # pressure conversion factor
			["Offset [N]","H",18,2, "N"], # force offset
			["Year","H",20,2, "y"], # acquitision year
			["Month","H",22,2, "m"], # acquisition month
			["Day","H",24,2, "d"], # acquisition day
			["Hour","H",26,2, "h"], # acquitiion hour
			["Min","H",28,2, "min"], # acquisition minute
			["Sec","H",30,2, "s"], # acquisition seconds
			["X Coord","d",32,8, "deg"], # ???
			["Y Coord","d",40,8, "deg"], # ???
			["Z Coord","d",48,8, "deg"], # ???
			["Battery [V]","d",56,8, "V"], # internal battery voltage
			["Speed [mm/s]","f",64,4, "mm/s"], # probing velocity
			["Loopsize","l",68,4, None], # ???
			["Waypoints","10l",72,40, None], # ???
			["Calstart","10H",112,20, None], # ???
			["Calend","10H",132,20, None], # ???
			["Length Comment","H",152,2, None], # length of comment chars
			["Comment","102s",154,102, None], # comment string
			["File Name","8s",256,8, None], # original file name
			["Latitude","f",264,4, "deg"], # gps latitude
			["Longitude","f",268,4, "deg"], # gps longitude
			["Altitude [cm]","f",272,4, "cm"], # gps altitude
			["PDOP","f",276,4, None], # ???
			["Northing","c",280,1, None], # northing string
			["Easting","c",281,1, None], # easting string
			["Num Sats","H",282,2, None], # number of gps satelites
			["Fix Mode","H",284,2, None], # gps fix mode
			["GPS State","c",286,1, None], # gps state
			["reserved 1","x",187,1, None], # reserved
			["X local","H",288,2, "deg"], # ???
			["Y local","H",290,2, "deg"], # ???
			["Z local","H",292,2, "m"], # ???
			["Theta local","H",294,2, "deg"], # ???
			["reserved 2","62x",296,62, None], # reserved
			["Force Samples","l",358,4, None], # numbers of force samples
			["Temperature Samples","l",362,4, None], # number of temperature samples
			["Kistler Range [pC]","H",366,2, "pC"], # Kistler range
			["Amp Range [pC]","H",368,2, "pC"], # amplifier range
			["Sensitivity [pC/N]","H",370,2, "pC/N"], # amplifier sensitivity
			["Temp Offset [K]","h",372,2, "Celsius"], # temperature offset
			["Hand Op","H",374,2, None], # ???
			["Diameter [um]","l",376,4, "um"], # probing tip diameter
			["Overload [N]","H",380,2, "N"], # force overload value
			["Sensor Type","c",382,1, None], # sensor type
			["Amp Type","c",383,1, None], # amp type
			["SMP Serial","H",384,2, None], # SMP serial
			["Length [mm]","H",386,2, "mm"], # SMP rod length
			["reserved 3","4x",388,4, None], # reserved
			["Sensor Serial","20s",392,20, None], # force sensor serial
			["Amp Serial","20s",412,20, None], # amp serial
			["reserved 4 ","80x",432,80, None]] # reserved

class Pnt():
	def __init__(self, filename, verbose=False):
		"""
		Create Pnt object from given filename.
		Input:
			-filename: path to file to parse
		Returns:
			-self.filename: Path to .pnt file [str]
			-self.data: force and displacement data [numpy array]
			-self.header:
			-self.units:
		Private:
			-self.__verbose__: print some additional information
		"""
		self.__verbose__ = verbose # verbosity
		self.units = [param[4] for param in PARAMTABLE]

		# create Pnt object from file
		self.fromFile(filename)


	def fromFile(self, fname):
		"""
		create Pnt object from file and return self
		"""
		self.filename = fname # path to .pnt file
		raw = self.getRaw() # read raw data
		self.header = self.getHeader(raw) # read header as dict
		self.data = self.getData(raw) # read data points
		return self

	def __str__(self):
		return self.printHeader() + "\n" + self.printData()

	def setVerbose(self, verbose=True):
		"""
		set verbosity
		"""
		self.__verbose__ = verbose
		return self.__verbose__

	def getRaw(self):
		"""
		Return raw data from .pnt file
		"""
		with open(self.filename,"rb") as f:
			raw = f.read()
			if self.__verbose__:
				print "Read %d bytes in %s" %(len(raw), self.filename)
			f.close()

		return raw

	def getHeader(self, raw=None):
		"""
		Read Header from raw data using the parameter table
		return header dict {param:value}, and list of paramater units
		"""
		if not raw:
			raw = self.getRaw()
		#read header values and return dict vwith parameter name : value
		header = {}
		for (key, fmt, start, length, unit) in PARAMTABLE:
			fmt = ">" + fmt
			end = start + length
			try:
				value = struct.unpack(fmt,raw[start:end])
				if len(value) == 1: # single value
					header[key] = value[0]
				elif len(value) == 0: # empty value
					header[key] = None
				else:
				 	header[key] = value
			except:
				raise IOError("Could not decode header entry %s at byte %d" %(key,start))

		#format some strings
		if header["Length Comment"]:
			header["Comment"] = header["Comment"][:header["Length Comment"]]
		else:
			header["Comment"] = ""

		header["File Name"] = header["File Name"].split("\x00")[0]
		header["Amp Serial"] = header["Amp Serial"].split("\x00")[0]
		header["Sensor Serial"] = header["Sensor Serial"].split("\x00")[0]
		header["Northing"] = header["Northing"].split("\x00")[0]
		header["Easting"] = header["Easting"].split("\x00")[0]
		header["GPS State"] = header["GPS State"].split("\x00")[0]

		# add sign to coordinates if required
		if header["Northing"] == "S":
			header["Latitude"] = - header["Latitude"]
		if header["Easting"] == "W":
			header["Longitude"] = - header["Longitude"]

		if self.__verbose__:
			print "decoded header of %s" %self.filename

		return header

	def printHeader(self):
		"""
		return header entries in alphanumerical order as formatted string
		"""
		msg = "Header:"
		for key,value in sorted(self.header.items()):
			msg += "\n{0}: {1}".format(key.ljust(15) , value)
		return msg

	def printData(self):
		"""
		return force displacement data formatted string
		"""
		msg = "x [mm]\ty [N]"
		for (x,y) in zip(self.data[:,0],self.data[:,1]):
			msg += "\n{:.3f}\t{:.3f}".format(x,y)
		return msg

	def writeHeader(self, fname=None):
		""""
		write header data to text file fname
		return fname
		"""
		if not fname:
			fname = self.filename.replace(".pnt", ".txt")
		fname = os.path.join(os.getcwd(),fname)

		with open(fname, "w") as f:
			f.write(	"#Automatic written Header from SnowMicroPen .pnt binary\n"
						"#SLF Institute for Snow and Avalanche Research\n#\n"
						"##################################\n#Header:\n##################################\n")

			for entry, value in sorted(self.header.items()):
				line = "%s %s\n" %(entry.ljust(15), str(value))
				f.write(line)
			if self.__verbose__:
				print "wrote header of %s to %s" %(self.filename, fname)
			f.close()

		return fname

	def getData(self, raw=None):
		"""
		get force and displacement data from pnt raw data
		return numpy ndarray:
		displacement [mm]: axis 0
		force [N]: axis 1
		"""
		if not raw:
			raw = self.getRaw()

		try:
			start = 512
			end = self.header["Force Samples"] * 2 + start
			frmt = ">" + str(self.header["Force Samples"]) + "h"
			data = struct.unpack(frmt, raw[start:end])
		except:
			raise IOError("Error while reading data points in %s" %self.filename)

		dx = self.header["Samples Dist [mm]"]
		data_x = numpy.arange(0, len(data)) * dx
		data_y = numpy.asarray(data) * self.header["CNV Force [N/mV]"] # convert mV to Force
		data = numpy.column_stack([data_x,data_y])

		if self.__verbose__:
			print "Read %d data points in %s" %(len(data_y),self.filename)
		return data

	def writePnt(self, fname=None):
		"""
		write .pnt file from Pnt class header infos and data
		return fname
		"""
		if not fname:
			fname = self.filename
		fname = os.path.join(os.getcwd(),fname)

		buff = "" # buffer string

		data = self.data[:,1] / self.header["CNV Force [N/mV]"] # convert N to mV

		# adapt header entries
		self.header["Force Samples"] = len(data) # correct the number of force samples if data have been modified
		self.header["Length Comment"] = len(self.header["Comment"])

		#pack header to buffer
		for (key, fmt, start, length, unit) in PARAMTABLE:
			fmt = ">" + fmt # big endian
			if type(self.header[key]) is tuple:
				buff += struct.pack(fmt, *self.header[key])
			elif "x" in fmt: # reserved spaces
				buff += length * struct.pack(">"+"s","\x00")
			else:
				buff += struct.pack(fmt, self.header[key])

		#pack data array to buffer
		buff += struct.pack(">"+len(data)*"h", *data)

		#write buffer to file
		with open(fname,"w+b") as f:
			f.write(buff)
			f.close()

		if self.__verbose__:
			print "wrote %d bytes to %s" %(len(buff),fname)

		return fname
