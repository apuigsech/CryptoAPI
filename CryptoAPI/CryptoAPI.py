#!/usr/bin/env python

# CryptoAPI: Python Crypto API implementation
#
# Copyright (c) 2014 - Albert Puigsech Galicia (albert@puigsech.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from CryptsyAPI import CryptsyAPI
from BittrexAPI import BittrexAPI

class CryptoAPI_iface(object):

	def balances(self, currency=None, cached=None):
		raise NotImplementedError( "Method not implemented" )

	def marketstatus(self, market=None, depth_level=None, cached=None):
		raise NotImplementedError( "Method not implemented" )

	def orders(self, market=None, cached=None):
		raise NotImplementedError( "Method not implemented" ) 

	def putorder(self, market, type, pricetype, amount, price=None, simulation=None):
		raise NotImplementedError( "Method not implemented" )

	def delorder(self, order_id=None, simulation=None):
		raise NotImplementedError( "Method not implemented" )


class CryptoAPI_cryptsy(CryptsyAPI, CryptoAPI_iface):
	def __init__(self, key, secret, simulation=False, cached=False):
		super(CryptoAPI_cryptsy, self).__init__(key, secret, simulation, cached)
		CryptoAPI_iface.__init__(self)

	def balances(self, currency=None, cached=None):
		if cached == None:
			cached = self.cached

		ret = {
			'available': {},
			'hold': {},
			'total': {},
		}

		info = self.getinfo(cached)['return']

		for i in info['balances_available']:
			if i == currency or (currency == None and (float(info['balances_available'][i]) > 0 or info['balances_hold'].has_key(i))):
				ret['available'][i] = float(info['balances_available'][i])
				ret['hold'][i] = float(info['balances_hold'][i]) if info['balances_hold'].has_key(i) else float(0)
				ret['total'][i] = ret['available'][i] + ret['hold'][i]

		return ret


	def marketstatus(self, market=None, depth_level=None, cached=None):
		if cached == None:
			cached = self.cached

		status = self.getmarkets(cached)['return']
		
		ret = {}

		for i in status:
			marketname = '{0}-{1}'.format(i['secondary_currency_code'], i['primary_currency_code'])
			if marketname == market or i['primary_currency_code'] == market or i['secondary_currency_code'] == market or market == None:
				ret[marketname] = {
					'id': int(i['marketid']),
					'last_price': float(i['last_trade']),
					'high_price': float(i['high_trade']),
					'low_price': float(i['low_trade']),
					'volume': float(i['current_volume']),
					'depth': None
				}
				if depth_level != None and depth_level > 0:
					depth = self.depth(i['marketid'], cached)['return']

					ret[marketname]['depth'] = {
						'buy': [],
						'sell': [],
					}

					for j in depth['buy'][0:depth_level]:
						ret[marketname]['depth']['buy'].append([float(j[0]),float(j[1])])
					for j in depth['sell'][0:depth_level]:
						ret[marketname]['depth']['sell'].append([float(j[0]),float(j[1])])

		return ret


	def orders(self, market=None, cached=None):
		if cached == None:
			cached = self.cached

		orders = self.allmyorders(cached)['return']

		ret = []

		for i in orders:
			marketname = self._getmarketfromid(i['marketid'])
			ret.append({
				'id': int(i['orderid']),
				'market': 'TBD',
				'price': i['price'],
				'amount': i['orig_quantity'],
				'remaining_amount': i['quantity'],
			})

		return ret


	def putorder(self, market, type, pricetype, amount, price=None, simulation=None):
		if simulation == None:
			simulation = self.simulation

		status = self.marketstatus(market, 1)
		print status

		if pricetype == 'market':
			price = 4294967296

		elif pricetype == 'best':
			if type == 'buy':
				price = status[market]['depth']['sell'][0][0]
			elif type == 'sell':
				price = status[market]['depth']['buy'][0][0]

		elif pricetype == 'border' or pricetype == 'overboder':
			if type == 'buy':
				price = status[market]['depth']['buy'][0][0]
			elif type == 'sell':
				price = status[market]['depth']['sell'][0][0]
			if pricetype == 'overboder':
				if type == 'buy':
					price += 0.00000001
				elif type == 'sell':
					price -= 0.00000001

		return self.createorder(status[market]['id'], type, amount, price)


	def delorder(self, order_id=None, simulation=None):
		return None


	def _getmarketfromid(self, id):
		markets = self.marketstatus(cached=True)
		for marketname in markets:
			if markets[marketname]['id'] == id:
				return marketname
		return None


	def _getidfrommarket(self, market):
		markets = self.marketstatus(cached=True)
		if markets.has_key(market):
			return markets[market]['id']
		else:
			return None
			

class CryptoAPI_bittrex(BittrexAPI, CryptoAPI_iface):
	def __init__(self, key, secret, simulation=False, cached=False):
		super(CryptoAPI_bittrex, self).__init__(key, secret, simulation, cached)


	def balances(self, currency=None, cached=None):
		if cached == None:
			cached = self.cached

		ret = {
			'available': {},
			'hold': {},
			'total': {},
		}

		if currency==None:
			info = self.getbalances(cached)['result']
		else:
			pass
			info = [self.getbalance(currency, cached)['result']]

		for i in info:
			ret['available'][i['Currency']] = float(i['Available'])
			ret['hold'][i['Currency']] = float(i['Pending'])
			ret['total'][i['Currency']] = float(i['Balance'])

		return ret


	def marketstatus(self, market=None, depth_level=None, cached=None):
		if cached == None:
			cached = self.cached

		ret = {}

		status = self.getmarkets(cached)['result']
		status = self.getmarketsummaries(cached)['result']

		for i in status:
			marketname = i['MarketName']
			#if marketname == market or market == i['BaseCurrency']  or market == i['MarketCurrency'] or market == None:
			if marketname == market or market in marketname or market == None:

				if i['Volume'] == None:
					i['Volume'] = 0

				ret[marketname] = {
					'id': marketname,
					'last_price': float(i['Last']),
					'high_price': float(str(i['High'])),  # FIX a bug on Bittrex data returned
					'low_price': float(i['Low']),
					'volume': float(i['Volume']),
					'depth': None
				}
				if depth_level != None and depth_level > 0:
					depth = self.getorderbook(marketname, 'both', depth_level, cached)['result']

					ret[marketname]['depth'] = {
						'buy': [],
						'sell': [],
					}

					for j in depth['buy'][0:depth_level]:
						ret[marketname]['depth']['buy'].append([float(j['Rate']),float(j['Quantity'])])
					for j in depth['sell'][0:depth_level]:
						ret[marketname]['depth']['sell'].append([float(j['Rate']),float(j['Quantity'])])

		return ret


	def orders(self, market=None, cached=None):
		if cached == None:
			cached = self.cached

		ret = []

		orders = self.getopenorders(market, cached)['return']

		for i in orders:
			marketname = self._getmarketfromid(i['marketid'])
			ret.append({
				'id': int(i['orderid']),
				'market': 'TBD',
				'price': i['price'],
				'amount': i['orig_quantity'],
				'remaining_amount': i['quantity'],
			})

		return ret



		pass


	def putorder(self, market, type, pricetype, amount, price=None, simulation=None):
		pass

	def delorder(self, order_id=None, simulation=None):
		pass


def CryptoAPI(type, key, secret, simulation=False, cached=False):
	# TODO Security: type validation
	code = 'CryptoAPI_{0}(key, secret, simulation, cached)'.format(type)
	api = eval(code)
	return api