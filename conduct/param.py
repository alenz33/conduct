# *****************************************************************************
# conduct - CONvenient Construction Tool
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Module authors:
#   Alexander Lenz <alexander.lenz@posteo.de>
#   Georg Brandl <georg@python.org>
#
# *****************************************************************************

import re

from os import path
from collections import Iterable


class Parameter(object):
    '''
    Some kind of parameter.

    No default means mandatory.
    '''
    def __init__(self, type=str, description='Undescribed', default=None):
        self.type = type
        self.description = description
        self.default = default

        if default is not None:
            self.validate(default)

    def validate(self, value):
        self.type(value)



# validators for parameter's type

def convdoc(conv):
    if isinstance(conv, type):
        return conv.__name__
    return conv.__doc__ or ''

class listof(object):

    def __init__(self, conv):
        self.__doc__ = 'a list of %s' % convdoc(conv)
        self.conv = conv

    def __call__(self, val=None):
        val = val if val is not None else []
        if not isinstance(val, (list, tuple)):
            raise ValueError('value needs to be a list')
        return list(map(self.conv, val))


class nonemptylistof(object):

    def __init__(self, conv):
        self.__doc__ = 'a non-empty list of %s' % convdoc(conv)
        self.conv = conv

    def __call__(self, val=None):
        if val is None:
            return [self.conv()]
        if not isinstance(val, (list, tuple)) or len(val) < 1:
            raise ValueError('value needs to be a nonempty list')
        return list(map(self.conv, val))


def nonemptystring(s):
    """a non-empty string"""
    if not isinstance(s, str) or s == '':
        raise ValueError('must be a non-empty string!')
    return s


class tupleof(object):

    def __init__(self, *types):
        if not types:
            raise ValueError('tupleof() needs some types as arguments')
        self.__doc__ = 'a tuple of (' + ', '.join(map(convdoc, types)) + ')'
        self.types = [typeconv for typeconv in types]

    def __call__(self, val=None):
        if val is None:
            return tuple(type() for type in self.types)
        if not isinstance(val, (list, tuple)) or not len(self.types) == len(val):
            raise ValueError('value needs to be a %d-tuple' % len(self.types))
        return tuple(t(v) for (t, v) in zip(self.types, val))


def limits(val=None):
    """a tuple of lower and upper limit"""
    val = val if val is not None else (0, 0)
    if not isinstance(val, (list, tuple)) or len(val) != 2:
        raise ValueError('value must be a list or tuple and have 2 elements')
    ll = float(val[0])
    ul = float(val[1])
    if not ll <= ul:
        raise ValueError('upper limit must be greater than lower limit')
    return (ll, ul)


class dictof(object):

    def __init__(self, keyconv, valconv):
        self.__doc__ = 'a dict of %s keys and %s values' % \
                       (convdoc(keyconv), convdoc(valconv))
        self.keyconv = keyconv
        self.valconv = valconv

    def __call__(self, val=None):
        val = val if val is not None else {}
        if not isinstance(val, dict):
            raise ValueError('value needs to be a dict')
        ret = {}
        for k, v in val.iteritems():
            ret[self.keyconv(k)] = self.valconv(v)
        return ret


class intrange(object):

    def __init__(self, fr, to):
        fr = int(fr)
        to = int(to)
        if not fr <= to:
            raise ValueError('intrange must fulfill from <= to, given was '
                             '[%f, %f]' % (fr, to))
        self.__doc__ = 'an integer in the range [%d, %d]' % (fr, to)
        self.fr = fr
        self.to = to

    def __call__(self, val=None):
        if val is None:
            return self.fr
        val = int(val)
        if not self.fr <= val <= self.to:
            raise ValueError('value needs to fulfill %d <= x <= %d' %
                             (self.fr, self.to))
        return val


class floatrange(object):

    def __init__(self, fr, to=None):
        fr = float(fr)
        if to is not None:
            to = float(to)
            if not fr <= to:
                raise ValueError('floatrange must fulfill from <= to, given was '
                                 '[%f, %f]' % (fr, to))
            self.__doc__ = 'a float in the range [%f, %f]' % (fr, to)
        else:
            self.__doc__ = 'a float >= %f' % fr
        self.fr = fr
        self.to = to

    def __call__(self, val=None):
        if val is None:
            return self.fr
        val = float(val)
        if self.to is not None:
            if not self.fr <= val <= self.to:
                raise ValueError('value needs to fulfill %d <= x <= %d' %
                                 (self.fr, self.to))
        else:
            if not self.fr <= val:
                raise ValueError('value needs to fulfill %d <= x' % self.fr)
        return val


class oneof(object):

    def __init__(self, *vals):
        self.__doc__ = 'one of ' + ', '.join(map(repr, vals))

        if len(vals) == 1 and isinstance(vals[0], Iterable):
            self.vals = vals[0]
        else:
            self.vals = vals

    def __call__(self, val=None):
        if val is None:
            return self.vals[0]
        if val not in self.vals:
            raise ValueError('invalid value: %r, must be one of %s' %
                             (val, ', '.join(map(repr, self.vals))))
        return val


class oneofdict(object):

    def __init__(self, vals):
        self.__doc__ = 'one of ' + ', '.join(map(repr, vals.values()))
        self.vals = vals

    def __call__(self, val=None):
        if val in self.vals:
            val = self.vals[val]
        elif val not in self.vals.values():
            raise ValueError('invalid value: %s, must be one of %s' %
                             (val, ', '.join(map(repr, self.vals.values()))))
        return val


class none_or(object):

    def __init__(self, conv):
        self.__doc__ = 'None or %s' % convdoc(conv)
        self.conv = conv

    def __call__(self, val=None):
        if val is None:
            return None
        return self.conv(val)

# see http://stackoverflow.com/questions/3217682/checking-validity-of-email-in-django-python
# for source

mailaddress_re = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"                # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
    r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+([A-Z]{2,99}|XN[A-Z0-9-]+)\.?$',   # domain
    re.IGNORECASE)


def mailaddress(val=None):
    """a valid mail address"""
    if val in ('', None):
        return ''
    parts = val.split('@')
    parts[-1] = parts[-1].encode('idna').decode('ascii')
    val = '@'.join(parts)
    if '>' in val and not val.strip().endswith('>'):
        raise ValueError('%r is not a valid email address' % val)
    if not mailaddress_re.match(val.strip().partition('<')[-1].rpartition('>')[0] or val):
        raise ValueError('%r is not a valid email address' % val)
    return val


def absolute_path(val=''):
    """an absolute file path"""
    val = str(val)
    if path.isabs(val):
        return val
    raise ValueError('%r is not a valid absolute path (should start with %r)' %
                     (val, path.sep))


def relative_path(val=''):
    """a relative path, may not use ../../.. tricks"""
    val = path.normpath(str(val))
    if path.isabs(val):
        raise ValueError('%r is not a valid relative path (should NOT start '
                         'with %r)' % (val, path.sep))
    if val[:2] != '..':
        return val
    raise ValueError('%r is not a valid relative path (traverses outside)' % val)


def expanded_path(val=''):
    return path.expanduser(path.expandvars(val))


def subdir(val=''):
    """a relative subdir (a string NOT containing any path.sep)"""
    val = str(val)
    for sep in [path.sep, '\\', '/']:
        if sep in val:
            raise ValueError('%r is not a valid subdirectory (contains a %r)' %
                             (val, sep))
    return val


def anytype(val=None):
    """any value"""
    return val


ipv4_re = re.compile(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
    r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)


def ipv4(val='0.0.0.0'):
    """a IP v4 address"""
    if val in ('', None):
        return ''
    val = str(val)
    res = ipv4_re.match(val)
    if not res or res.group() != res.string:
        raise ValueError('%r is not a valid IPv4 address' % val)
    return val


def host(val=''):
    """a host[:port] value"""
    if not isinstance(val, str):
        raise ValueError('must be a string!')
    if val.count(':') > 1:
        raise ValueError('%r is not in the form host_name[:port]')
    if ':' in val:
        _, p = val.split(':')
        try:
            p = int(p)
            if not 0 < p < 65536:
                raise ValueError()
        except ValueError:
            raise ValueError('%r does not contain a valid port number' % val)
    return val
