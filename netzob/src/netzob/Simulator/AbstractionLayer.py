#-*- coding: utf-8 -*-

#+---------------------------------------------------------------------------+
#|          01001110 01100101 01110100 01111010 01101111 01100010            |
#|                                                                           |
#|               Netzob : Inferring communication protocols                  |
#+---------------------------------------------------------------------------+
#| Copyright (C) 2011-2017 Georges Bossert and Frédéric Guihéry              |
#| This program is free software: you can redistribute it and/or modify      |
#| it under the terms of the GNU General Public License as published by      |
#| the Free Software Foundation, either version 3 of the License, or         |
#| (at your option) any later version.                                       |
#|                                                                           |
#| This program is distributed in the hope that it will be useful,           |
#| but WITHOUT ANY WARRANTY; without even the implied warranty of            |
#| MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              |
#| GNU General Public License for more details.                              |
#|                                                                           |
#| You should have received a copy of the GNU General Public License         |
#| along with this program. If not, see <http://www.gnu.org/licenses/>.      |
#+---------------------------------------------------------------------------+
#| @url      : http://www.netzob.org                                         |
#| @contact  : contact@netzob.org                                            |
#| @sponsors : Amossys, http://www.amossys.fr                                |
#|             Supélec, http://www.rennes.supelec.fr/ren/rd/cidre/           |
#|             ANSSI,   https://www.ssi.gouv.fr                              |
#+---------------------------------------------------------------------------+

#+---------------------------------------------------------------------------+
#| File contributors :                                                       |
#|       - Georges Bossert <georges.bossert (a) supelec.fr>                  |
#|       - Frédéric Guihéry <frederic.guihery (a) amossys.fr>                |
#+---------------------------------------------------------------------------+

#+---------------------------------------------------------------------------+
#| Standard library imports                                                  |
#+---------------------------------------------------------------------------+
import time
import socket

#+---------------------------------------------------------------------------+
#| Related third party imports                                               |
#+---------------------------------------------------------------------------+

#+---------------------------------------------------------------------------+
#| Local application imports                                                 |
#+---------------------------------------------------------------------------+
from netzob.Common.Utils.Decorators import typeCheck, public_api, NetzobLogger
from netzob.Model.Vocabulary.Symbol import Symbol
from netzob.Model.Vocabulary.Field import Field
from netzob.Model.Vocabulary.EmptySymbol import EmptySymbol
from netzob.Model.Vocabulary.Domain.Variables.Memory import Memory
from netzob.Model.Vocabulary.Domain.Specializer.MessageSpecializer import MessageSpecializer
from netzob.Model.Vocabulary.Domain.Parser.MessageParser import MessageParser
from netzob.Model.Vocabulary.Domain.Parser.FlowParser import FlowParser
from netzob.Model.Vocabulary.Messages.RawMessage import RawMessage
from netzob.Model.Vocabulary.UnknownSymbol import UnknownSymbol
from netzob.Common.Utils.DataAlignment.DataAlignment import DataAlignment


class SymbolBadSettingsException(Exception):
    pass


class Operation(Enum):
    """Tells the direction of the symbol.

    """
    READ = 'read'
    """Indicates that the symbol has been received from the channel."""
    WRITE = 'write'
    """Indicates that the symbol has been sent on the channel."""
    __repr__ = Enum.__str__


@NetzobLogger
class AbstractionLayer(object):
    """An abstraction layer specializes a symbol into a message before
    emitting it and, on the other way, abstracts a received message
    into a symbol.

    The AbstractionLayer constructor expects some parameters:

    :param channel: This parameter is the underlying communication channel (such as IPChannel,
                    UDPClient...).
    :param symbols: This parameter is the list of permitted symbols during translation from/to
                    concrete messages.
    :param memory: This parameter is a memory used to store variable values during specialization
                   and abstraction of successive symbols, especially to handle
                   inter-symbol relationships. If None, a local memory is
                   created by default and used internally.
    :type channel: :class:`AbstractChannel <netzob.Model.Simulator.AbstractChannel.AbstractChannel>`, required
    :type symbols: a :class:`list` of :class:`Symbol <netzob.Model.Vocabular.Symbol.Symbol>`, required
    :type memory: :class:`Memory <netzob.Model.Vocabular.Domain.Variables.Memory.Memory>`, optional


    The AbstractionLayer class provides the following public variables:

    :var channel: The underlying communication channel (such as IPChannel,
                  UDPClient...).
    :var symbols: The list of permitted symbols during translation from/to
                  concrete messages.
    :var memory: A memory used to store variable values during specialization
                 and abstraction of successive symbols, especially to handle
                 inter-symbol relationships.
    :vartype channel: :class:`AbstractChannel <netzob.Model.Simulator.AbstractChannel.AbstractChannel>`
    :vartype symbols: a :class:`list` of :class:`Symbol <netzob.Model.Vocabular.Symbol.Symbol>`
    :vartype memory: :class:`Memory <netzob.Model.Vocabular.Domain.Variables.Memory.Memory>`


    **Usage example of the abstraction layer**

    The following code shows a usage of the abstraction layer class,
    where two UDP channels (client and server) are built and transport
    just one permitted symbol:

    >>> from netzob.all import *
    >>> symbol = Symbol([Field(b"Hello Kurt !")], name = "Symbol_Hello")
    >>> channelIn = UDPServer(localIP="127.0.0.1", localPort=8889, timeout=1.)
    >>> abstractionLayerIn = AbstractionLayer(channelIn, [symbol])
    >>> abstractionLayerIn.openChannel()
    >>> channelOut = UDPClient(remoteIP="127.0.0.1", remotePort=8889, timeout=1.)
    >>> abstractionLayerOut = AbstractionLayer(channelOut, [symbol])
    >>> abstractionLayerOut.openChannel()
    >>> (data, data_len, data_structure) = abstractionLayerOut.writeSymbol(symbol)
    >>> data_len
    12
    >>> (received_symbol, received_data, received_structure) = abstractionLayerIn.readSymbol()
    >>> received_symbol.name
    'Symbol_Hello'
    >>> received_data
    b'Hello Kurt !'


    **Handling message flow within the abstraction layer**

    The following example demonstrates that the abstraction layer can
    also handle a message flow:

    >>> from netzob.all import *
    >>> symbolflow = Symbol([Field(b"Hello Kurt !Whats up ?")], name = "Symbol Flow")
    >>> symbol1 = Symbol([Field(b"Hello Kurt !")], name = "Symbol_Hello")
    >>> symbol2 = Symbol([Field(b"Whats up ?")], name = "Symbol_WUP")
    >>> channelIn = UDPServer(localIP="127.0.0.1", localPort=8889, timeout=1.)
    >>> abstractionLayerIn = AbstractionLayer(channelIn, [symbol1, symbol2])
    >>> abstractionLayerIn.openChannel()
    >>> channelOut = UDPClient(remoteIP="127.0.0.1", remotePort=8889, timeout=1.)
    >>> abstractionLayerOut = AbstractionLayer(channelOut, [symbolflow])
    >>> abstractionLayerOut.openChannel()
    >>> (data, data_len, data_structure) = abstractionLayerOut.writeSymbol(symbolflow)
    >>> data_len
    22
    >>> (received_symbols, received_data) = abstractionLayerIn.readSymbols()
    >>> received_symbols
    [Symbol_Hello, Symbol_WUP]


    **Relationships between the environment and the produced messages**

    The following example shows how to define a relationship between a
    message to send and an environment variable, then how to leverage this
    relationship when using the abstraction layer.

    >>> from netzob.all import *
    >>> # Environment variable definition
    >>> memory1 = Memory()
    >>> env1 = Data(String(), name="env1")
    >>> memory1.memorize(env1, String("John").value)
    >>>
    >>> # Symbol definition
    >>> f7 = Field(domain=String("master"), name="F7")
    >>> f8 = Field(domain=String(">"), name="F8")
    >>> f9 = Field(domain=Value(env1), name="F9")
    >>> symbol = Symbol(fields=[f7, f8, f9], name="Symbol_Hello")
    >>>
    >>> # Creation of channels with dedicated abstraction layer
    >>> channelIn = UDPServer(localIP="127.0.0.1", localPort=8889, timeout=1.)
    >>> abstractionLayerIn = AbstractionLayer(channelIn, [symbol], memory1)
    >>> abstractionLayerIn.openChannel()
    >>> channelOut = UDPClient(remoteIP="127.0.0.1", remotePort=8889, timeout=1.)
    >>> abstractionLayerOut = AbstractionLayer(channelOut, [symbol], memory1)
    >>> abstractionLayerOut.openChannel()
    >>>
    >>> # Sending of a symbol containing a data coming from the environment
    >>> (data, data_len, data_structure) = abstractionLayerOut.writeSymbol(symbol)
    >>> data_len
    11
    >>> (received_symbol, received_data, received_structure) = abstractionLayerIn.readSymbol()
    >>> received_symbol.name
    'Symbol_Hello'
    >>> received_data
    b'master>John'

    """

    def __init__(self, channel, symbols, memory=None, presets=None, cbk_data=None):
        self.channel = channel
        self.symbols = symbols
        if memory is None:
            self.memory = Memory()
        else:
            self.memory = memory
        self.presets = presets
        self.cbk_data = cbk_data

        # Instanciate inner instance variables
        self.specializer = MessageSpecializer(memory=self.memory)
        self.parser = MessageParser(memory=self.memory)
        self.flow_parser = FlowParser(memory=self.memory)

        # Variables used to keep track of the last sent and received symbols and associated messages
        self.last_sent_symbol = None
        self.last_sent_message = None
        self.last_sent_structure = None
        self.last_received_symbol = None
        self.last_received_message = None
        self.last_received_structure = None

        self.__queue_input = Queue()

    @public_api
    @typeCheck(Symbol)
    def writeSymbol(self, symbol, rate=None, duration=None, presets=None, fuzz=None, actor=None, cbk_action=[]):
        """Write the specified symbol on the communication channel
        after specializing it into a contextualized message.

        :param symbol: The symbol to write on the channel.
        :param rate: This specifies the bandwidth in octets to respect
                     during traffic emission (should be used with
                     :attr:`duration` parameter). Default value is None (no
                     rate).
        :param duration: This indicates for how many seconds the symbol is
                         continuously written on the channel. Default
                         value is None (write only once).
        :param presets: This specifies how to parameterize the emitted
                        symbol. The expected content of this dict is
                        specified in :meth:`Symbol.specialize \
                        <netzob.Model.Vocabulary.Symbol.Symbol.specialize>`.
                        Default is None.
        :param fuzz: A fuzzing configuration used during the specialization process. Values
                     in this configuration will override any field
                     definition, constraints, relationship
                     dependencies or parameterized fields. See
                     :class:`Fuzz <netzob.Fuzzing.Fuzz.Fuzz>`
                     for a complete explanation of its use for fuzzing
                     purpose.
                     Default is None.
        :type symbol: :class:`Symbol <netzob.Model.Vocabulary.Symbol.Symbol>`, required
        :type rate: :class:`int`, optional
        :type duration: :class:`int`, optional
        :type presets: ~typing.Dict[
                       ~typing.Union[str,~netzob.Model.Vocabulary.Field.Field],
                       ~typing.Union[~bitarray.bitarray,bytes,
                       ~netzob.Model.Vocabulary.Types.AbstractType.AbstractType]],
                       optional
        :type fuzz: :class:`Fuzz <netzob.Fuzzing.Fuzz.Fuzz>`, optional
        :raise: :class:`TypeError` if a parameter is not valid and :class:`Exception` if an exception occurs.

        """

        if symbol is None:
            raise TypeError("The symbol to write on the channel cannot be None")

        if self.presets is not None:
            if presets is not None:
                presets.update(self.presets)
            else:
                presets = self.presets

        data = b''
        data_len = 0
        data_structure = {}
        if duration is None:
            (data, data_len, data_structure) = self._writeSymbol(symbol, presets=presets, fuzz=fuzz, actor=actor, cbk_action=cbk_action)
        else:

            t_start = time.time()
            t_elapsed = 0
            t_delta = 0
            while True:

                t_elapsed = time.time() - t_start
                if t_elapsed > duration:
                    break

                # Specialize the symbol and send it over the channel
                (data, data_len_tmp, data_structure) = self._writeSymbol(symbol, presets=presets, fuzz=fuzz, actor=actor, cbk_action=cbk_action)
                data_len += data_len_tmp

                if rate is None:
                    t_tmp = t_elapsed
                    t_elapsed = time.time() - t_start
                    t_delta += t_elapsed - t_tmp
                else:
                    # Wait some time to that we follow a specific rate
                    while True:
                        t_tmp = t_elapsed
                        t_elapsed = time.time() - t_start
                        t_delta += t_elapsed - t_tmp

                        if (data_len / t_elapsed) > rate:
                            time.sleep(0.001)
                        else:
                            break

                # Show some log every seconds
                if t_delta > 1:
                    t_delta = 0
                    if rate is None:
                        self._logger.debug("Current rate: {} ko/s, sent data: {} ko, nb seconds elapsed: {}".format(round((data_len / t_elapsed) / 1024, 2),
                                                                                                                    round(data_len / 1024, 2),
                                                                                                                    round(t_elapsed, 2)))
                    else:
                        self._logger.fatal("Rate rule: {} ko/s, current rate: {} ko/s, sent data: {} ko, nb seconds elapsed: {}".format(round(rate / 1024, 2),
                                                                                                                                        round((data_len / t_elapsed) / 1024, 2),
                                                                                                                                        round(data_len / 1024, 2),
                                                                                                                                        round(t_elapsed, 2)))
        return (data, data_len, data_structure)

    def _writeSymbol(self, symbol, presets=None, fuzz=None, actor=None, cbk_action=[]):
        """Write the specified symbol on the communication channel after
        specializing it into a contextualized message.

        :param symbol: The symbol to write on the channel.
        :param presets: This specifies how to parameterize the emitted
                        symbol. The expected content of this dict is
                        specified in :meth:`Symbol.specialize \
                        <netzob.Model.Vocabulary.Symbol.Symbol.specialize>`.
        :param fuzz: A fuzzing configuration used during the specialization process. Values
                     in this configuration will override any field
                     definition, constraints, relationship
                     dependencies or parameterized fields. See
                     :class:`Fuzz <netzob.Fuzzing.Fuzz.Fuzz>`
                     for a complete explanation of its use for fuzzing
                     purpose.
        :type symbol: :class:`Symbol <netzob.Model.Vocabulary.Symbol.Symbol>`
        :type presets: :class:`dict`, optional
        :type fuzz: :class:`Fuzz <netzob.Fuzzing.Fuzz.Fuzz>`, optional
        :raise: :class:`TypeError` if parameter is not valid and :class:`Exception` if an exception occurs.

        """
        data_len = 0
        if isinstance(symbol, EmptySymbol):
            self._logger.debug("Symbol to write is an EmptySymbol. So nothing to do.".format(symbol.name))
            return (b'', data_len, OrderedDict())

        self._logger.debug("Specializing symbol '{0}' (id={1}).".format(symbol.name, id(symbol)))

        self.specializer.presets = presets
        self.specializer.fuzz = fuzz
        path = next(self.specializer.specializeSymbol(symbol))

        data = path.generatedContent.tobytes()

        # Build data structure (i.e. a dict containing data content for each field)
        data_structure = OrderedDict()
        for field in symbol.getLeafFields():
            if path.hasData(field.domain):
                field_data = path.getData(field.domain)
            else:
                field_data = b''
            data_structure[field.name] = field_data

        self.specializer.presets = None  # This is needed, in order to avoid applying the preset configuration on an already preseted symbol
        # Regarding the fuzz attribute, as its behavior is different from preset, we don't have to set it to None

        self.memory = self.specializer.memory
        self.parser.memory = self.memory

        self._logger.debug("Writing the following data to the commnunication channel: '{}'".format(data))
        self._logger.debug("Writing the following symbol to the commnunication channel: '{}'".format(symbol.name))

        try:
            data_len = self.channel.write(data)
        except socket.timeout:
            self._logger.debug("Timeout on channel.write(...)")
            raise
        except Exception as e:
            self._logger.debug("Exception on channel.write(...): '{}'".format(e))
            raise

        self.last_sent_symbol = symbol
        self.last_sent_message = data
        self.last_sent_structure = data_structure

        for cbk in cbk_action:
            self._logger.debug("[actor='{}'] A callback function is defined at the end of the transition".format(str(actor)))
            cbk(symbol, data, data_structure, Operation.WRITE, actor)

        return (data, data_len, data_structure)

    @public_api
    def readSymbols(self):
        """Read a flow from the abstraction layer and abstract it in one or
        more consecutive symbols.

        The timeout attribute of the underlying channel is important
        as it represents the amount of time (in seconds) above which
        no receipt of a message triggers the receipt of an
        :class:`EmptySymbol
        <netzob.Model.Vocabulary.EmptySymbol.EmptySymbol>`.

        """

        self._logger.debug("Reading data from communication channel...")
        data = self.channel.read()
        self._logger.debug("Received : {}".format(repr(data)))

        symbols = []

        # if we read some bytes, we try to abstract them
        if len(data) > 0:
            try:
                symbols_and_data = self.flow_parser.parseFlow(
                    RawMessage(data), self.symbols)
                for (symbol, alignment) in symbols_and_data:
                    symbols.append(symbol)
            except Exception as e:
                self._logger.error(e)

            if len(symbols) > 0:
                self.memory = self.flow_parser.memory
                self.specializer.memory = self.memory
        else:
            symbols.append(EmptySymbol())

        if len(symbols) == 0 and len(data) > 0:
            msg = RawMessage(data)
            symbols.append(UnknownSymbol(message=msg))

        return (symbols, data)

    @public_api
    def readSymbol(self, symbols_presets=None, timeout=5.0, actor=None):
        """Read a message from the abstraction layer and abstract it
        into a symbol.

        The timeout attribute of the underlying channel is important
        as it represents the amount of time (in seconds) above which
        no receipt of a message triggers the receipt of an
        :class:`EmptySymbol
        <netzob.Model.Vocabulary.EmptySymbol.EmptySymbol>`.
        """

        self._logger.debug("Reading data from communication channel...")

        try:
            data = self.channel.read()
        except socket.timeout:
            self._logger.debug("Timeout on channel.read()")
            raise
        except Exception as e:
            self._logger.debug("Exception on channel.read(): '{}'".format(e))
            raise

        self._logger.debug("Received: {}".format(repr(data)))

        symbol = None
        data_structure = {}

        # if we read some bytes, we try to abstract them in a symbol
        if len(data) > 0:
            for potentialSymbol in self.symbols:
                try:
                    aligned_data = DataAlignment.align([data], potentialSymbol, encoded=False, messageParser=self.parser)

                    symbol = potentialSymbol
                    self.memory = self.parser.memory
                    self.specializer.memory = self.memory
                    break
                except Exception as e:
                    self._logger.debug(e)

        # Build data structure (i.e. a dict containing data content for each field)
        if symbol is not None:
            data_structure = OrderedDict()
            for fields_value in aligned_data:
                for i, field_value in enumerate(fields_value):
                    data_structure[aligned_data.headers[i]] = field_value

        if symbol is None and len(data) > 0:
            msg = RawMessage(data)
            symbol = UnknownSymbol(message=msg)
        elif symbol is None and len(data) == 0:
            symbol = EmptySymbol()

        self.last_received_symbol = symbol
        self.last_received_message = data
        self.last_received_structure = data_structure

        self._logger.debug("Receiving the following data from the commnunication channel: '{}'".format(data))
        self._logger.debug("Receiving the following symbol from the commnunication channel: '{}'".format(symbol.name))

        # Check symbol regarding its expected presets
        if not isinstance(symbol, (UnknownSymbol, EmptySymbol)):
            if symbols_presets is not None:
                if not self._check_presets(symbol, data_structure, symbols_presets):
                    self._logger.debug("Receive good symbol but with wrong setting")
                    raise SymbolBadSettingsException()

        return (symbol, data, data_structure)

    def _check_presets(self, symbol, data_structure, symbols_presets):
        self._logger.debug("Checking symbol consistency regarding its expected presets, for symbol '{}'".format(symbol))

        if symbol not in symbols_presets.keys():
            return True

        result = True
        symbol_presets = symbols_presets[symbol]
        for (field, field_presets) in symbol_presets.items():
            if isinstance(field, Field):
                field_name = field.name
            else:
                field_name = field
            if field_name in data_structure.keys():
                expected_value = field_presets.tobytes()
                observed_value = data_structure[field_name]
                self._logger.debug("Checking field consistence, for field '{}'".format(field_name))
                if expected_value == observed_value:
                    self._logger.debug("Field '{}' consistency is ok: expected value '{}' == observed value '{}'".format(field_name, expected_value, observed_value))
                else:
                    self._logger.debug("Field '{}' consistency is not ok: expected value '{}' != observed value '{}'".format(field_name, expected_value, observed_value))
                    result = False
                    break

        if result:
            self._logger.debug("Symbol '{}' consistency is ok".format(symbol))
        else:
            self._logger.debug("Symbol '{}' consistency is not ok".format(symbol))
        return result

    @public_api
    def openChannel(self):
        """Open the underlying communication channel.

        """

        self.channel.open()
        self._logger.debug("Communication channel opened.")

    @public_api
    def closeChannel(self):
        """Close the underlying communication channel.

        """

        self.channel.close()
        self._logger.debug("Communication channel close.")

    @public_api
    def reset(self):
        """Reset the abstraction layer (i.e. its internal memory as well as the internal parsers).

        """

        self._logger.debug("Reseting abstraction layer")
        self.memory = Memory()
        self.specializer = MessageSpecializer(memory=self.memory)
        self.parser = MessageParser(memory=self.memory)
        self.flow_parser = FlowParser(memory=self.memory)
