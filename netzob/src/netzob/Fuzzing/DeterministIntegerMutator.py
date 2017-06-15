# -*- coding: utf-8 -*-

# +---------------------------------------------------------------------------+
# |          01001110 01100101 01110100 01111010 01101111 01100010            |
# |                                                                           |
# |               Netzob : Inferring communication protocols                  |
# +---------------------------------------------------------------------------+
# | Copyright (C) 2011-2017 Georges Bossert and Frédéric Guihéry              |
# | This program is free software: you can redistribute it and/or modify      |
# | it under the terms of the GNU General Public License as published by      |
# | the Free Software Foundation, either version 3 of the License, or         |
# | (at your option) any later version.                                       |
# |                                                                           |
# | This program is distributed in the hope that it will be useful,           |
# | but WITHOUT ANY WARRANTY; without even the implied warranty of            |
# | MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              |
# | GNU General Public License for more details.                              |
# |                                                                           |
# | You should have received a copy of the GNU General Public License         |
# | along with this program. If not, see <http://www.gnu.org/licenses/>.      |
# +---------------------------------------------------------------------------+
# | @url      : http://www.netzob.org                                         |
# | @contact  : contact@netzob.org                                            |
# | @sponsors : Amossys, http://www.amossys.fr                                |
# |             Supélec, http://www.rennes.supelec.fr/ren/rd/cidre/           |
# |             ANSSI,   https://www.ssi.gouv.fr                              |
# +---------------------------------------------------------------------------+

# +---------------------------------------------------------------------------+
# | File contributors :                                                       |
# |       - Frédéric Guihéry <frederic.guihery (a) amossys.fr>                |
# |       - Rémy Delion <remy.delion (a) amossys.fr>                          |
# +---------------------------------------------------------------------------+

# +---------------------------------------------------------------------------+
# | Standard library imports                                                  |
# +---------------------------------------------------------------------------+
from typing import Iterable

# +---------------------------------------------------------------------------+
# | Related third party imports                                               |
# +---------------------------------------------------------------------------+

# +---------------------------------------------------------------------------+
# | Local application imports                                                 |
# +---------------------------------------------------------------------------+
from netzob.Fuzzing.Mutator import Mutator
from netzob.Common.Utils.Decorators import typeCheck
from netzob.Fuzzing.DeterministGenerator import DeterministGenerator
from netzob.Model.Vocabulary.Types.Integer import Integer
from netzob.Model.Vocabulary.Types.AbstractType import AbstractType, Sign, UnitSize
from netzob.Model.Vocabulary.AbstractField import AbstractField
from netzob.Model.Vocabulary.Domain.Variables.AbstractVariable import AbstractVariable


class DeterministIntegerMutator(Mutator):
    r"""The integer mutator, using determinist generator.
    The seed is an arbitrary value used to set the position of the next
    integer to return from the values list, when calling generate().
    This position is the seed modulo the number of elements in the list of
    generated values.

    The DeterministIntegerMutator constructor expects some parameters:

    :param domain: The domain of the field to mutate.
    :param interval: The scope of values to generate.
        If set to **Mutator.DEFAULT_INTERVAL**, the values will be generate
        between the min and max values of the domain.
        If set to **Mutator.FULL_INTERVAL**, the values will be generate in
        [0, 2^N-1], where N is the bitsize (storage) of the field.
        If it is an tuple of integers (min, max), the values will be generate
        between min and max.
        Default value is **Mutator.DEFAULT_INTERVAL**.
    :param mode: If set to **Mutator.GENERATE**, the generate() method will be
        used to produce the value.
        If set to **Mutator.MUTATE**, the mutate() method will be used to
        produce the value (not implemented).
        Default value is **Mutator.GENERATE**.
    :param bitsize: The size in bits of the memory on which the generated
        values have to be encoded.
    :type domain: :class:`AbstractVariable
        <netzob.Model.Vocabulary.Domain.Variables.AbstractVariable>`, required
    :type interval: :class:`int` or :class:`tuple`, optional
    :type mode: :class:`int`, optional
    :type bitsize: :class:`int`, optional

    The following example shows how to generate an 8bits integer in [-128, +127]
    interval:

    >>> from netzob.all import *
    >>> fieldInt1 = Field(Integer())
    >>> mutator1 = DeterministIntegerMutator(fieldInt1.domain)
    >>> mutator1.seed=52
    >>> mutator1.generate()
    b'\x03'

    The following example shows how to generate an 8bits integer in [-10, +5]
    interval:

    >>> fieldInt2 = Field(Integer(interval=(-10, 5)))
    >>> mutator2 = DeterministIntegerMutator(fieldInt2.domain)
    >>> mutator2.seed=42
    >>> mutator2.generate()
    b'\xfd'

    The following example shows how to generate an 8bits integer in
    [-32768, +32767] interval:

    >>> fieldInt3 = Field(Integer(unitSize=UnitSize.SIZE_16))
    >>> mutator3 = DeterministIntegerMutator(fieldInt3.domain)
    >>> mutator3.seed=430
    >>> mutator3.generate()
    b'\xff\xc1'

    """

    def __init__(self,
                 domain,
                 interval=Mutator.DEFAULT_INTERVAL,
                 mode=Mutator.GENERATE,
                 bitsize=None):
        # Sanity checks
        if domain is None:
            raise Exception("Domain should be known to initialize a mutator")
        if not isinstance(domain, AbstractVariable):
            raise Exception("Mutator domain should be of type AbstractVariable. Received object: '{}'".format(domain))
        if not hasattr(domain, 'dataType'):
            raise Exception("Mutator domain should have a dataType Integer")
        if not isinstance(domain.dataType, Integer):
            raise Exception("Mutator domain dataType should be an Integer, not '{}'".format(type(domain.dataType)))

        # Call parent init
        super().__init__(domain=domain, mode=mode)

        # Find min and max potential values for interval
        minValue = 0
        maxValue = 0
        if isinstance(interval, tuple) and len(interval) == 2 and isinstance(interval[0], int) and isinstance(interval[1], int):
            # Handle desired interval according to the storage space of the domain dataType
            minValue = max(interval[0], domain.dataType.getMinStorageValue())
            maxValue = min(interval[1], domain.dataType.getMaxStorageValue())
        elif interval == Mutator.DEFAULT_INTERVAL and hasattr(domain, 'dataType'):
            minValue = domain.dataType.getMinValue()
            maxValue = domain.dataType.getMaxValue()
        elif interval == Mutator.FULL_INTERVAL and hasattr(domain, 'dataType'):
            minValue = domain.dataType.getMinStorageValue()
            maxValue = domain.dataType.getMaxStorageValue()
        else:
            raise Exception("Not enough information to generate the mutated data")
        self._minValue = minValue
        self._maxValue = maxValue

        if bitsize is not None:
            if not isinstance(bitsize, int) or bitsize <=0:
                raise ValueError("{} is not a valid bitsize value".format(bitsize))
        self._bitsize = bitsize
        if self._bitsize is None:
            self._bitsize = domain.dataType.unitSize.value
        if self._minValue >= 0:
            if self._maxValue > 2**self._bitsize - 1:
                raise ValueError("The upper bound {} is too large and cannot be encoded on {} bits".format(self._maxValue, self._bitsize))
        else:
            if self._maxValue > 2**(self._bitsize - 1) - 1:
                raise ValueError("The upper bound {} is too large and cannot be encoded on {} bits".format(self._maxValue, self._bitsize))
            if self._minValue < -2**(self._bitsize - 1):
                raise ValueError("The lower bound {} is too small and cannot be encoded on {} bits".format(self._minValue, self._bitsize))

        # Initialize values to generate
        self._ng = DeterministGenerator()
        self._ng.createValues(self._minValue,
                              self._maxValue,
                              self._bitsize,
                              domain.dataType.sign == Sign.SIGNED)

    @property
    def seed(self):
        """
        Property (getter/setter).
        The seed initializes the position of the value to return
        from the list of generated integer values, mudulo the number of values.

        :type: :class:`int`
        """
        return self._seed

    @seed.setter
    @typeCheck(int)
    def seed(self, seedValue):
        self._seed = seedValue
        self._ng.seed = self._seed

    def reset(self):
        """Reset the position in the generated list and set the mutation
        counter to 0
        """
        self._ng.reset()
        self.resetCurrentCounter()

    def getValueAt(self, position):
        """Returns the value at the given position in the list of determinist values.
        if **position** is outside of the list, it returns **None**.

        :return: the value at the given position
        :rtype: :class:`int`
        """
        value = self._ng.getValueAt(position)
        return Integer.decode(value,
                              unitSize=self.domain.dataType.unitSize,
                              endianness=self.domain.dataType.endianness,
                              sign=self.domain.dataType.sign)

    def getNbValues(self):
        """Returns the number of determinist values generated for the field domain.

        :return: the number of determinist values
        :rtype: :class:`int`
        """
        return len(self._ng.values)

    def generateInt(self):
        """This method returns an integer value produced by a determinist generator.

        :return: the generated integer value
        :rtype: :class:`int`
        """
        return self._ng.getNewValue()

    def generate(self):
        """This is the fuzz generation method of the integer field domain.
        It uses a determinist generator to produce the value.

        :return: a generated content represented with bytes
        :rtype: :class:`bytes`
        """
        # Call parent generate() method
        super().generate()

        return Integer.decode(self.generateInt(),
                              unitSize=self.domain.dataType.unitSize,
                              endianness=self.domain.dataType.endianness,
                              sign=self.domain.dataType.sign)
