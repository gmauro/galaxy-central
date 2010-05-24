#Dan Blankenberg
import math
import string
import transform
from sequence import SequencingRead
from fasta import fastaSequence

class fastqSequencingRead( SequencingRead ):
    format = 'sanger' #sanger is default
    ascii_min = 33
    ascii_max = 126
    quality_min = 0
    quality_max = 93
    score_system = 'phred' #phred or solexa
    sequence_space = 'base' #base or color
    @classmethod
    def get_class_by_format( cls, format ):
        assert format in FASTQ_FORMATS, 'Unknown format type specified: %s' % format
        return FASTQ_FORMATS[ format ]
    @classmethod
    def convert_score_phred_to_solexa( cls, decimal_score_list ):
        def phred_to_solexa( score ):
            if score <= 0: #can't take log10( 1 - 1 ); make <= 0 into -5
                return -5
            return int( round( 10.0 * math.log10( math.pow( 10.0, ( float( score ) / 10.0 ) ) - 1.0 ) ) )
        return map( phred_to_solexa, decimal_score_list )
    @classmethod
    def convert_score_solexa_to_phred( cls, decimal_score_list ):
        def solexa_to_phred( score ):
            return int( round( 10.0 * math.log10( math.pow( 10.0, ( float( score ) / 10.0 ) ) + 1.0 ) ) )
        return map( solexa_to_phred, decimal_score_list )
    @classmethod
    def restrict_scores_to_valid_range( cls, decimal_score_list ):
        def restrict_score( score ):
            return max( min( score, cls.quality_max ), cls.quality_min )
        return map( restrict_score, decimal_score_list )
    @classmethod
    def convert_base_to_color_space( cls, sequence ):
        return cls.color_space_converter.to_color_space( sequence )
    @classmethod
    def convert_color_to_base_space( cls, sequence ):
        return cls.color_space_converter.to_base_space( sequence )
    def is_ascii_encoded( self ):
        #as per fastq definition only decimal quality strings can have spaces (and TABs for our purposes) in them (and must have a trailing space)
        if ' ' in self.quality:
            return False
        if '\t' in self.quality:
            return False
        return True
    def get_ascii_quality_scores( self ):
        if self.is_ascii_encoded():
            return list( self.quality )
        else:
            quality = self.quality.rstrip() #decimal scores should have a trailing space
            if quality:
                try:
                    return [ chr( int( val ) + self.ascii_min - self.quality_min ) for val in quality.split() ]
                except ValueError, e:
                    raise ValueError( 'Error Parsing quality String. ASCII quality strings cannot contain spaces (%s): %s' % ( self.quality, e ) )
            else:
                return []
    def get_decimal_quality_scores( self ):
        if self.is_ascii_encoded():
            return [ ord( val ) - self.ascii_min + self.quality_min for val in self.quality ]
        else:
            quality = self.quality.rstrip() #decimal scores should have a trailing space
            if quality:
                return [ int( val ) for val in quality.split() if val.strip() ]
            else:
                return []
    def convert_read_to_format( self, format, force_quality_encoding = None ):
        assert format in FASTQ_FORMATS, 'Unknown format type specified: %s' % format
        assert force_quality_encoding in [ None, 'ascii', 'decimal' ], 'Invalid force_quality_encoding: %s' % force_quality_encoding
        new_class = FASTQ_FORMATS[ format ]
        new_read = new_class()
        new_read.identifier = self.identifier
        if self.sequence_space == new_class.sequence_space:
            new_read.sequence = self.sequence
        else:
            if self.sequence_space == 'base':
                new_read.sequence = self.convert_base_to_color_space( self.sequence )
            else:
                new_read.sequence = self.convert_color_to_base_space( self.sequence )
        new_read.description = self.description
        if self.score_system != new_read.score_system:
            if self.score_system == 'phred':
                score_list = self.convert_score_phred_to_solexa( self.get_decimal_quality_scores() )
            else:
                score_list = self.convert_score_solexa_to_phred( self.get_decimal_quality_scores() )
        else:
            score_list = self.get_decimal_quality_scores()
        new_read.quality = "%s " % " ".join( map( str, new_class.restrict_scores_to_valid_range( score_list ) ) ) #need trailing space to be valid decimal fastq
        if force_quality_encoding is None:
            if self.is_ascii_encoded():
                new_encoding = 'ascii'
            else:
                new_encoding = 'decimal'
        else:
            new_encoding = force_quality_encoding
        if new_encoding == 'ascii':
            new_read.quality = "".join( new_read.get_ascii_quality_scores() )
        return new_read
    def get_sequence( self ):
        return self.sequence
    def slice( self, left_column_offset, right_column_offset ):
        new_read = fastqSequencingRead.get_class_by_format( self.format )()
        new_read.identifier = self.identifier
        new_read.sequence = self.get_sequence()[left_column_offset:right_column_offset]
        new_read.description = self.description
        if self.is_ascii_encoded():
            new_read.quality = self.quality[left_column_offset:right_column_offset]
        else:
            quality = map( str, self.get_decimal_quality_scores()[left_column_offset:right_column_offset] )
            if quality:
                new_read.quality = "%s " % " ".join( quality )
            else:
                new_read.quality = ''
        return new_read
    def is_valid_format( self ):
        if self.is_ascii_encoded():
            for val in self.get_ascii_quality_scores():
                val = ord( val )
                if val < self.ascii_min or val > self.ascii_max:
                    return False
        else:
            for val in self.get_decimal_quality_scores():
                if val < self.quality_min or val > self.quality_max:
                    return False
        if not self.is_valid_sequence():
            return False
        return True
    def is_valid_sequence( self ):
        for base in self.get_sequence():
            if base not in self.valid_sequence_list:
                return False
        return True
    def insufficient_quality_length( self ):
        return len( self.get_ascii_quality_scores() ) < len( self.sequence )
    def assert_sequence_quality_lengths( self ):
        qual_len = len( self.get_ascii_quality_scores() )
        seq_len = len( self.sequence )
        assert qual_len == seq_len, "Invalid FASTQ file: quality score length (%i) does not match sequence length (%i)" % ( qual_len, seq_len )
    def reverse( self, clone = True ):
        #need to override how decimal quality scores are reversed
        if clone:
            rval = self.clone()
        else:
            rval = self
        rval.sequence = transform.reverse( self.sequence )
        if rval.is_ascii_encoded():
            rval.quality = rval.quality[::-1]
        else:
            rval.quality = reversed( rval.get_decimal_quality_scores() )
            rval.quality = "%s " % " ".join( map( str, rval.quality ) )
        return rval

class fastqSangerRead( fastqSequencingRead ):
    format = 'sanger'
    ascii_min = 33
    ascii_max = 126
    quality_min = 0
    quality_max = 93
    score_system = 'phred'
    sequence_space = 'base'

class fastqIlluminaRead( fastqSequencingRead ):
    format = 'illumina'
    ascii_min = 64
    ascii_max = 126
    quality_min = 0
    quality_max = 62
    score_system = 'phred'
    sequence_space = 'base'

class fastqSolexaRead( fastqSequencingRead ):
    format = 'solexa'
    ascii_min = 59
    ascii_max = 126
    quality_min = -5
    quality_max = 62
    score_system = 'solexa'
    sequence_space = 'base'
    
class fastqCSSangerRead( fastqSequencingRead ):
    format = 'cssanger' #color space
    ascii_min = 33
    ascii_max = 126
    quality_min = 0
    quality_max = 93
    score_system = 'phred'
    sequence_space = 'color'
    valid_sequence_list = map( str, range( 7 ) ) + [ '.' ]
    def __len__( self ):
        if self.has_adapter_base(): #Adapter base is not counted in length of read
            return len( self.sequence ) - 1
        return fastqSequencingRead.__len__( self )
    def has_adapter_base( self ):
        if self.sequence and self.sequence[0] in string.letters: #adapter base must be a letter
            return True
        return False
    def insufficient_quality_length( self ):
        if self.has_adapter_base():
            return len( self.get_ascii_quality_scores() ) + 1 < len( self.sequence )
        return fastqSequencingRead.insufficient_quality_length( self )
    def assert_sequence_quality_lengths( self ):
        if self.has_adapter_base():
            qual_len = len( self.get_ascii_quality_scores() )
            seq_len = len( self.sequence )
            assert qual_len + 1 == seq_len, "Invalid FASTQ file: quality score length (%i) does not match sequence length (%i with adapter base)" % ( qual_len, seq_len )
        else:
            return fastqSequencingRead.assert_sequence_quality_lengths( self )
    def get_sequence( self ):
        if self.has_adapter_base():
            return self.sequence[1:]
        return self.sequence
    def reverse( self, clone = True ):
        #need to override how color space is reversed
        if clone:
            rval = self.clone()
        else:
            rval = self
        if rval.has_adapter_base():
            adapter = rval.sequence[0]
            #sequence = rval.sequence[1:]
            rval.sequence = self.color_space_converter.to_color_space( transform.reverse( self.color_space_converter.to_base_space( rval.sequence ) ), adapter_base = adapter )
        else:
            rval.sequence = transform.reverse( rval.sequence )
        
        if rval.is_ascii_encoded():
            rval.quality = rval.quality[::-1]
        else:
            rval.quality = reversed( rval.get_decimal_quality_scores() )
            rval.quality = "%s " % " ".join( map( str, rval.quality ) )
        return rval
    def complement( self, clone = True ):
        #need to override how color space is complemented
        if clone:
            rval = self.clone()
        else:
            rval = self
        if rval.has_adapter_base(): #No adapter, color space stays the same
            adapter = rval.sequence[0]
            sequence = rval.sequence[1:]
            if adapter.lower() != 'u':
                adapter = transform.DNA_complement( adapter )
            else:
                adapter = transform.RNA_complement( adapter )
            rval.sequence = "%s%s" % ( adapter, sequence )
        return rval
    def change_adapter( self, new_adapter, clone = True ):
        #if new_adapter is empty, remove adapter, otherwise replace with new_adapter
        if clone:
            rval = self.clone()
        else:
            rval = self
        if rval.has_adapter_base():
            if new_adapter:
                if new_adapter != rval.sequence[0]:
                    rval.sequence = rval.color_space_converter.to_color_space( rval.color_space_converter.to_base_space( rval.sequence ), adapter_base = new_adapter )
            else:
                rval.sequence = rval.sequence[1:]
        elif new_adapter:
            rval.sequence = "%s%s" % ( new_adapter, rval.sequence )
        return rval


FASTQ_FORMATS = {}
for format in [ fastqIlluminaRead, fastqSolexaRead, fastqSangerRead, fastqCSSangerRead ]:
    FASTQ_FORMATS[ format.format ] = format


class fastqAggregator( object ):
    VALID_FORMATS = FASTQ_FORMATS.keys()
    def __init__( self,  ):
        self.ascii_values_used = [] #quick lookup of all ascii chars used
        self.seq_lens = {} #counts of seqs by read len
        self.nuc_index_quality = [] #counts of scores by read column
        self.nuc_index_base = [] #counts of bases by read column
    def consume_read( self, fastq_read ):
        #ascii values used
        for val in fastq_read.get_ascii_quality_scores():
            if val not in self.ascii_values_used:
                self.ascii_values_used.append( val )
        #lengths
        seq_len = len( fastq_read )
        self.seq_lens[ seq_len ] = self.seq_lens.get( seq_len, 0 ) + 1
        #decimal qualities by column
        for i, val in enumerate( fastq_read.get_decimal_quality_scores() ):
            if i == len( self.nuc_index_quality ):
                self.nuc_index_quality.append( {} )
            self.nuc_index_quality[ i ][ val ] = self.nuc_index_quality[ i ].get( val, 0 ) + 1
        #bases by column
        for i, nuc in enumerate( fastq_read.get_sequence() ):
            if i == len( self.nuc_index_base ):
                self.nuc_index_base.append( {} )
            nuc = nuc.upper()
            self.nuc_index_base[ i ][ nuc ] = self.nuc_index_base[ i ].get( nuc, 0 ) + 1
    def get_valid_formats( self, check_list = None ):
        if not check_list:
            check_list = self.VALID_FORMATS
        rval = []
        sequence = []
        for nuc_dict in self.nuc_index_base:
            for nuc in nuc_dict.keys():
                if nuc not in sequence:
                    sequence.append( nuc )
        sequence = "".join( sequence )
        quality = "".join( self.ascii_values_used )
        for fastq_format in check_list:
            fastq_read = fastqSequencingRead.get_class_by_format( fastq_format )()
            fastq_read.quality = quality
            fastq_read.sequence = sequence
            if fastq_read.is_valid_format():
                rval.append( fastq_format )
        return rval
    def get_ascii_range( self ):
        return ( min( self.ascii_values_used ), max( self.ascii_values_used ) )
    def get_decimal_range( self ):
        decimal_values_used = []
        for scores in self.nuc_index_quality:
            decimal_values_used.extend( scores.keys() )
        return ( min( decimal_values_used ), max( decimal_values_used ) )
    def get_length_counts( self ):
        return self.seq_lens
    def get_max_read_length( self ):
        return len( self.nuc_index_quality )
    def get_read_count_for_column( self, column ):
        if column >= len( self.nuc_index_quality ):
            return 0
        return sum( self.nuc_index_quality[ column ].values() )
    def get_read_count( self ):
        return self.get_read_count_for_column( 0 )
    def get_base_counts_for_column( self, column ):
        return self.nuc_index_base[ column ]
    def get_score_list_for_column( self, column ):
        return self.nuc_index_quality[ column ].keys()
    def get_score_min_for_column( self, column ):
        return min( self.nuc_index_quality[ column ].keys() )
    def get_score_max_for_column( self, column ):
        return max( self.nuc_index_quality[ column ].keys() )
    def get_score_sum_for_column( self, column ):
        return sum( score * count for score, count in self.nuc_index_quality[ column ].iteritems() )
    def get_score_at_position_for_column( self, column, position ):
        score_value_dict = self.nuc_index_quality[ column ]
        scores = sorted( score_value_dict.keys() )
        for score in scores:
            if score_value_dict[ score ] <= position:
                position -= score_value_dict[ score ]
            else:
                return score
    def get_summary_statistics_for_column( self, i ):
        def _get_med_pos( size ):
            halfed = int( size / 2 )
            if size % 2 == 1:
                return [ halfed ]
            return[ halfed - 1, halfed ]
        read_count = self.get_read_count_for_column( i )
        
        min_score = self.get_score_min_for_column( i )
        max_score = self.get_score_max_for_column( i )
        sum_score = self.get_score_sum_for_column( i )
        mean_score = float( sum_score ) / float( read_count )
        #get positions
        med_pos = _get_med_pos( read_count )
        if 0 in med_pos:
            q1_pos = [ 0 ]
            q3_pos = [ read_count - 1 ]
        else:
            q1_pos = _get_med_pos( min( med_pos ) )
            q3_pos = []
            for pos in q1_pos:
                q3_pos.append( max( med_pos ) + 1 + pos )
        #get scores at position
        med_score = float( sum( [ self.get_score_at_position_for_column( i, pos ) for pos in med_pos ] ) ) / float( len( med_pos ) )
        q1 = float( sum( [ self.get_score_at_position_for_column( i, pos ) for pos in q1_pos ] ) ) / float( len( q1_pos ) )
        q3 = float( sum( [ self.get_score_at_position_for_column( i, pos ) for pos in q3_pos ] ) ) / float( len( q3_pos ) )
        #determine iqr and step
        iqr = q3 - q1
        step = 1.5 * iqr
        
        #Determine whiskers and outliers
        outliers = []
        score_list = sorted( self.get_score_list_for_column( i ) )
        left_whisker = q1 - step
        for score in score_list:
            if left_whisker <= score:
                left_whisker = score
                break
            else:
                outliers.append( score )
        
        right_whisker = q3 + step
        score_list.reverse()
        for score in score_list:
            if right_whisker >= score:
                right_whisker = score
                break
            else:
                outliers.append( score )
        
        column_stats = { 'read_count': read_count, 
                         'min_score': min_score, 
                         'max_score': max_score, 
                         'sum_score': sum_score, 
                         'mean_score': mean_score, 
                         'q1': q1, 
                         'med_score': med_score, 
                         'q3': q3, 
                         'iqr': iqr, 
                         'left_whisker': left_whisker, 
                         'right_whisker': right_whisker,
                         'outliers': outliers }
        return column_stats

class fastqReader( object ):
    def __init__( self, fh, format = 'sanger' ):
        self.file = fh
        self.format = format
    def close( self ):
        return self.file.close()
    def next(self):
        while True:
            fastq_header = self.file.readline()
            if not fastq_header:
                raise StopIteration
            fastq_header = fastq_header.rstrip( '\n\r' )
            #remove empty lines, apparently extra new lines at end of file is common?
            if fastq_header:
                break
                
        assert fastq_header.startswith( '@' ), 'Invalid fastq header: %s' % fastq_header
        rval = fastqSequencingRead.get_class_by_format( self.format )()        
        rval.identifier = fastq_header
        while True:
            line = self.file.readline()
            if not line:
                raise Exception( 'Invalid FASTQ file: could not parse second instance of sequence identifier.' )
            line = line.rstrip( '\n\r' )
            if line.startswith( '+' ) and ( len( line ) == 1 or line[1:].startswith( fastq_header[1:] ) ):
                rval.description = line
                break
            rval.append_sequence( line )
        while rval.insufficient_quality_length():
            line = self.file.readline()
            if not line:
                break
            rval.append_quality( line )
        rval.assert_sequence_quality_lengths()
        return rval
    def __iter__( self ):
        while True:
            yield self.next()

class fastqNamedReader( object ):
    def __init__( self, fh, format = 'sanger' ):
        self.file = fh
        self.format = format
        self.reader = fastqReader( self.file, self.format )
        #self.last_offset = self.file.tell()
        self.offset_dict = {}
        self.eof = False
    def close( self ):
        return self.file.close()
    def get( self, sequence_id ):
        if not isinstance( sequence_id, basestring ):
            sequence_id = sequence_id.identifier
        rval = None
        if sequence_id in self.offset_dict:
            initial_offset = self.file.tell()
            seq_offset = self.offset_dict[ sequence_id ].pop( 0 )
            if not self.offset_dict[ sequence_id ]:
                del self.offset_dict[ sequence_id ]
            self.file.seek( seq_offset )
            rval = self.reader.next()
            #assert rval.identifier == sequence_id, 'seq id mismatch' #should be able to remove this
            self.file.seek( initial_offset )
        else:
            while True:
                offset = self.file.tell()
                try:
                    fastq_read = self.reader.next()
                except StopIteration:
                    self.eof = True
                    break #eof, id not found, will return None
                if fastq_read.identifier == sequence_id:
                    rval = fastq_read
                    break
                else:
                    if fastq_read.identifier not in self.offset_dict:
                        self.offset_dict[ fastq_read.identifier ] = []
                    self.offset_dict[ fastq_read.identifier ].append( offset )
        return rval
    def has_data( self ):
        #returns a string representation of remaining data, or empty string (False) if no data remaining
        eof = self.eof
        count = 0
        rval = ''
        if self.offset_dict:
            count = sum( map( len, self.offset_dict.values() ) )
        if not eof:
            offset = self.file.tell()
            try:
                fastq_read = self.reader.next()
            except StopIteration:
                eof = True
            self.file.seek( offset )
        if count:
            rval = "There were %i known sequence reads not utilized. "
        if not eof:
            rval = "%s%s" % ( rval, "An additional unknown number of reads exist in the input that were not utilized." )
        return rval

class fastqWriter( object ):
    def __init__( self, fh, format = None, force_quality_encoding = None ):
        self.file = fh
        self.format = format
        self.force_quality_encoding = force_quality_encoding
    def write( self, fastq_read ):
        if self.format:
            fastq_read = fastq_read.convert_read_to_format( self.format, force_quality_encoding = self.force_quality_encoding )
        self.file.write( str( fastq_read ) )
    def close( self ):
        return self.file.close()

class fastqJoiner( object ):
    def __init__( self, format, force_quality_encoding = None ):
        self.format = format
        self.force_quality_encoding = force_quality_encoding
    def join( self, read1, read2 ):
        if read1.identifier.endswith( '/2' ) and read2.identifier.endswith( '/1' ):
            #swap 1 and 2
            tmp = read1
            read1 = read2
            read2 = tmp
            del tmp
        if read1.identifier.endswith( '/1' ) and read2.identifier.endswith( '/2' ):
            identifier = read1.identifier[:-2]
        else:
            identifier = read1.identifier
        
        #use force quality encoding, if not present force to encoding of first read
        force_quality_encoding = self.force_quality_encoding
        if not force_quality_encoding:
            if read1.is_ascii_encoded():
                force_quality_encoding = 'ascii'
            else:
                force_quality_encoding = 'decimal'
        
        new_read1 = read1.convert_read_to_format( self.format, force_quality_encoding = force_quality_encoding )
        new_read2 = read2.convert_read_to_format( self.format, force_quality_encoding = force_quality_encoding )
        rval = FASTQ_FORMATS[ self.format ]()
        rval.identifier = identifier
        if len( read1.description ) > 1:
            rval.description = "+%s" % ( identifier[1:] )
        else:
            rval.description = '+'
        if rval.sequence_space == 'color':
            #need to handle color space joining differently
            #convert to nuc space, join, then convert back
            rval.sequence = rval.convert_base_to_color_space( new_read1.convert_color_to_base_space( new_read1.sequence ) + new_read2.convert_color_to_base_space( new_read2.sequence ) )
        else:
            rval.sequence = new_read1.sequence + new_read2.sequence
        if force_quality_encoding == 'ascii':
            rval.quality = new_read1.quality + new_read2.quality
        else:
            rval.quality = "%s %s" % ( new_read1.quality.strip(), new_read2.quality.strip() )
        return rval
    def get_paired_identifier( self, fastq_read ):
        identifier = fastq_read.identifier
        if identifier[-2] == '/':
            if identifier[-1] == "1":
                identifier = "%s2" % identifier[:-1]
            elif identifier[-1] == "2":
                identifier = "%s1" % identifier[:-1]
        return identifier

class fastqSplitter( object ):   
    def split( self, fastq_read ):
        length = len( fastq_read )
        #Only reads of even lengths can be split
        if length % 2 != 0:
            return None, None
        half = int( length / 2 )
        read1 = fastq_read.slice( 0, half )
        read1.identifier += "/1"
        if len( read1.description ) > 1:
            read1.description += "/1"
        read2 = fastq_read.slice( half, None )
        read2.identifier += "/2"
        if len( read2.description ) > 1:
            read2.description += "/2"
        return read1, read2

class fastqCombiner( object ):
    def __init__( self, format ):
        self.format = format
    def combine(self, fasta_seq, quality_seq ):
        fastq_read = fastqSequencingRead.get_class_by_format( self.format )()
        fastq_read.identifier = "@%s" % fasta_seq.identifier[1:]
        fastq_read.description = '+'
        fastq_read.sequence = fasta_seq.sequence
        fastq_read.quality = quality_seq.sequence
        return fastq_read

class fastqFakeFastaScoreReader( object ):
    def __init__( self, format = 'sanger', quality_encoding = None ):
        self.fastq_read = fastqSequencingRead.get_class_by_format( format )()
        if quality_encoding != 'decimal':
            quality_encoding = 'ascii'
        self.quality_encoding = quality_encoding
    def close( self ):
        return #nothing to close
    def get( self, sequence ):
        assert isinstance( sequence, fastaSequence ), 'fastqFakeFastaScoreReader requires a fastaSequence object as the parameter'
        #add sequence to fastq_read, then get_sequence(), color space adapters do not have quality score values
        self.fastq_read.sequence = sequence.sequence
        new_sequence = fastaSequence()
        new_sequence.identifier = sequence.identifier
        if self.quality_encoding == 'ascii':
            new_sequence.sequence = chr( self.fastq_read.ascii_max ) * len( self.fastq_read.get_sequence() )
        else:
            new_sequence.sequence = ( "%i " % self.fastq_read.quality_max ) * len( self.fastq_read.get_sequence() )
        return new_sequence
    def has_data( self ):
        return '' #No actual data exist, none can be remaining
