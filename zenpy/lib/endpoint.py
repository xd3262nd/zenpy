from datetime import datetime

__author__ = 'facetoe'


class BaseEndpoint(object):
	def __init__(self, endpoint, sideload=None):
		self.endpoint = endpoint
		self.sideload = sideload or []

	@staticmethod
	def _single(endpoint, user_id):
		return "%s/%s%s" % (endpoint, user_id, '.json')

	def _many(self, endpoint, user_ids):
		return "%s/%s%s" % (endpoint, 'show_many.json?ids=', self._format_many(user_ids))

	def _destroy_many(self, endpoint, ids):
		return "%s/%s%s" % (endpoint, 'destroy_many.json?ids=', self._format_many(ids))

	@staticmethod
	def _format(**kwargs):
		return '+'.join(['%s%s' % (key, value) for (key, value) in kwargs.items()])

	@staticmethod
	def _format_many(items):
		return ",".join([str(i) for i in items])

	def _format_sideload(self, items):
		if isinstance(items, basestring):
			items = [items]
		return '?include=' + self._format_many(items)


class PrimaryEndpoint(BaseEndpoint):
	def __call__(self, **kwargs):
		query = ""
		modifiers = []
		for key, value in kwargs.iteritems():
			if key == 'id':
				query += self._single(self.endpoint, value)
			elif key == 'ids':
				query += self._many(self.endpoint, value)
			elif key == 'destroy_ids':
				query += self._destroy_many(self.endpoint, value)
			elif key in ('sort_by', 'sort_order'):
				modifiers.append((key, value))

		if modifiers:
			query += '&' + "&".join(["%s=%s" % (k, v) for k, v in modifiers])

		if self.endpoint not in query:
			query = self.endpoint + '.json' + query

		if 'sideload' in kwargs and not kwargs['sideload']:
			return query
		else:
			return query + self._format_sideload(self.sideload)


class SecondaryEndpoint(BaseEndpoint):
	def __call__(self, **kwargs):
		return self.endpoint % kwargs


class SearchEndpoint(BaseEndpoint):
	def __call__(self, **kwargs):

		renamed_kwargs = dict()
		for key, value in kwargs.iteritems():
			if isinstance(value, datetime):
				kwargs[key] = value.strftime("%Y-%m-%d")
			elif isinstance(value, list):
				value = self._format_many(value)

			if '_after' in key:
				renamed_kwargs[key.replace('_after', '>')] = kwargs[key]
			elif '_before' in key:
				renamed_kwargs[key.replace('_before', '<')] = kwargs[key]
			elif '_greater_than' in key:
				renamed_kwargs[key.replace('_greater_than', '>')] = kwargs[key]
			elif '_less_than' in key:
				renamed_kwargs[key.replace('_less_than', '<')] = kwargs[key]
			else:
				renamed_kwargs.update({key + ':': value})  # Equal to , eg subject:party

		return self.endpoint + self._format(**renamed_kwargs)


class Endpoint(object):
	def __init__(self):
		self.users = PrimaryEndpoint('users', ['organizations', 'abilities', 'roles', 'identities', 'groups'])
		self.users.groups = SecondaryEndpoint('users/%(id)s/groups.json')
		self.users.organizations = SecondaryEndpoint('users/%(id)s/organizations.json')
		self.users.requested = SecondaryEndpoint('users/%(id)s/tickets/requested.json')
		self.users.cced = SecondaryEndpoint('users/%(id)s/tickets/ccd.json')
		self.users.assigned = SecondaryEndpoint('users/%(id)s/tickets/assigned.json')
		self.groups = PrimaryEndpoint('groups', ['users'])
		self.brands = PrimaryEndpoint('brands')
		self.topics = PrimaryEndpoint('topics')
		self.tickets = PrimaryEndpoint('tickets', ['users', 'groups', 'organizations'])
		self.tickets.organizations = SecondaryEndpoint('organizations/%(id)s/tickets.json')
		self.tickets.comments = SecondaryEndpoint('tickets/%(id)s/comments.json')
		self.tickets.recent = SecondaryEndpoint('tickets/recent.json')
		self.attachments = PrimaryEndpoint('attachments')
		self.organizations = PrimaryEndpoint('organizations')
		self.search = SearchEndpoint('search.json?query=')
