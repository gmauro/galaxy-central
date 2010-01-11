#! /usr/bin/python

"""
Runs Bowtie on single-end or paired-end data.
For use with Bowtie v. 0.12.1

usage: bowtie_wrapper.py [options]
    -t, --threads=t: The number of threads to run
    -i, --input1=i: The (forward or single-end) reads file in Sanger FASTQ format
    -I, --input2=I: The reverse reads file in Sanger FASTQ format
    -o, --output=o: The output file
    -4, --dataType=4: The type of data (SOLiD or Solexa)
    -2, --paired=2: Whether the data is single- or paired-end
    -g, --genomeSource=g: The type of reference provided
    -r, --ref=r: The reference genome to use or index
    -s, --skip=s: Skip the first n reads
    -a, --alignLimit=a: Only align the first n reads
    -T, --trimH=T: Trim n bases from high-quality (left) end of each read before alignment
    -L, --trimL=L: Trim n bases from low-quality (right) end of each read before alignment
    -m, --mismatchSeed=m: Maximum number of mismatches permitted in the seed
    -M, --mismatchQual=M: Maximum permitted total of quality values at mismatched read positions
    -l, --seedLen=l: Seed length
    -n, --rounding=n: Whether or not to round to the nearest 10 and saturating at 30
    -P, --maqSoapAlign=P: Choose MAQ- or SOAP-like alignment policy
    -w, --tryHard=: Whether or not to try as hard as possible to find valid alignments when they exist
    -v, --valAlign=v: Report up to n valid arguments per read
    -V, --allValAligns=V: Whether or not to report all valid alignments per read
    -G, --suppressAlign=G: Suppress all alignments for a read if more than n reportable alignments exist
    -b, --best=b: Whether or not to make Bowtie guarantee that reported singleton alignments are 'best' in terms of stratum and in terms of the quality values at the mismatched positions
    -B, --maxBacktracks=B: Maximum number of backtracks permitted when aligning a read
    -R, --strata=R: Whether or not to report only those alignments that fall in the best stratum if many valid alignments exist and are reportable
    -j, --minInsert=j: Minimum insert size for valid paired-end alignments
    -J, --maxInsert=J: Maximum insert size for valid paired-end alignments
    -O, --mateOrient=O: The upstream/downstream mate orientation for valid paired-end alignment against the forward reference strand
    -A, --maxAlignAttempt=A: Maximum number of attempts Bowtie will make to match an alignment for one mate with an alignment for the opposite mate
    -f, --forwardAlign=f: Whether or not to attempt to align the forward reference strand
    -E, --reverseAlign=E: Whether or not to attempt to align the reverse-complement reference strand
    -F, --offrate=F: Override the offrate of the index to n
    -8, --snpphred=8: SNP penalty on Phred scale
    -6, --snpfrac=6: Fraction of sites expected to be SNP sites
    -7, --keepends=7: Keep extreme-end nucleotides and qualities
    -S, --seed=S: Seed for pseudo-random number generator
    -d, --dbkey=d: Dbkey of reference genome
    -C, --params=C: Whether to use default or specified parameters
    -u, --iauto_b=u: Automatic or specified behavior
    -K, --ipacked=K: Whether or not to use a packed representation for DNA strings
    -Q, --ibmax=Q: Maximum number of suffixes allowed in a block
    -Y, --ibmaxdivn=Y: Maximum number of suffixes allowed in a block as a fraction of the length of the reference
    -D, --idcv=D: The period for the difference-cover sample
    -U, --inodc=U: Whether or not to disable the use of the difference-cover sample
    -y, --inoref=y: Whether or not to build the part of the reference index used only in paired-end alignment
    -z, --ioffrate=z: How many rows get marked during annotation of some or all of the Burrows-Wheeler rows
    -W, --iftab=W: The size of the lookup table used to calculate an initial Burrows-Wheeler range with respect to the first n characters of the query
    -X, --intoa=X: Whether or not to convert Ns in the reference sequence to As
    -N, --iendian=N: Endianness to use when serializing integers to the index file
    -Z, --iseed=Z: Seed for the pseudorandom number generator
    -c, --icutoff=c: Number of first bases of the reference sequence to index
    -x, --indexSettings=x: Whether or not indexing options are to be set
    -H, --suppressHeader=H: Suppress header
"""

import optparse, os, shutil, sys, tempfile

def stop_err( msg ):
    sys.stderr.write( "%s\n" % msg )
    sys.exit()
 
def __main__():
    #Parse Command Line
    parser = optparse.OptionParser()
    parser.add_option( '-t', '--threads', dest='threads', help='The number of threads to run' )
    parser.add_option( '-4', '--dataType', dest='dataType', help='The type of data (SOLiD or Solexa)' )
    parser.add_option( '-i', '--input1', dest='input1', help='The (forward or single-end) reads file in Sanger FASTQ format' )
    parser.add_option( '-I', '--input2', dest='input2', help='The reverse reads file in Sanger FASTQ format' )
    parser.add_option( '-o', '--output', dest='output', help='The output file' )
    parser.add_option( '-2', '--paired', dest='paired', help='Whether the data is single- or paired-end' )
    parser.add_option( '-g', '--genomeSource', dest='genomeSource', help='The type of reference provided' )
    parser.add_option( '-r', '--ref', dest='ref', help='The reference genome to use or index' )
    parser.add_option( '-s', '--skip', dest='skip', help='Skip the first n reads' )
    parser.add_option( '-a', '--alignLimit', dest='alignLimit', help='Only align the first n reads' )
    parser.add_option( '-T', '--trimH', dest='trimH', help='Trim n bases from high-quality (left) end of each read before alignment' )
    parser.add_option( '-L', '--trimL', dest='trimL', help='Trim n bases from low-quality (right) end of each read before alignment' )
    parser.add_option( '-m', '--mismatchSeed', dest='mismatchSeed', help='Maximum number of mismatches permitted in the seed' )
    parser.add_option( '-M', '--mismatchQual', dest='mismatchQual', help='Maximum permitted total of quality values at mismatched read positions' )
    parser.add_option( '-l', '--seedLen', dest='seedLen', help='Seed length' )
    parser.add_option( '-n', '--rounding', dest='rounding', help='Whether or not to round to the nearest 10 and saturating at 30' )
    parser.add_option( '-P', '--maqSoapAlign', dest='maqSoapAlign', help='Choose MAQ- or SOAP-like alignment policy' )
    parser.add_option( '-w', '--tryHard', dest='tryHard', help='Whether or not to try as hard as possible to find valid alignments when they exist' )
    parser.add_option( '-v', '--valAlign', dest='valAlign', help='Report up to n valid arguments per read' )
    parser.add_option( '-V', '--allValAligns', dest='allValAligns', help='Whether or not to report all valid alignments per read' )
    parser.add_option( '-G', '--suppressAlign', dest='suppressAlign', help='Suppress all alignments for a read if more than n reportable alignments exist' )
    parser.add_option( '-b', '--best', dest='best', help="Whether or not to make Bowtie guarantee that reported singleton alignments are 'best' in terms of stratum and in terms of the quality values at the mismatched positions" )
    parser.add_option( '-B', '--maxBacktracks', dest='maxBacktracks', help='Maximum number of backtracks permitted when aligning a read' )
    parser.add_option( '-R', '--strata', dest='strata', help='Whether or not to report only those alignments that fall in the best stratum if many valid alignments exist and are reportable' )
    parser.add_option( '-j', '--minInsert', dest='minInsert', help='Minimum insert size for valid paired-end alignments' )
    parser.add_option( '-J', '--maxInsert', dest='maxInsert', help='Maximum insert size for valid paired-end alignments' )
    parser.add_option( '-O', '--mateOrient', dest='mateOrient', help='The upstream/downstream mate orientation for valid paired-end alignment against the forward reference strand' )
    parser.add_option( '-A', '--maxAlignAttempt', dest='maxAlignAttempt', help='Maximum number of attempts Bowtie will make to match an alignment for one mate with an alignment for the opposite mate' )
    parser.add_option( '-f', '--forwardAlign', dest='forwardAlign', help='Whether or not to attempt to align the forward reference strand' )
    parser.add_option( '-E', '--reverseAlign', dest='reverseAlign', help='Whether or not to attempt to align the reverse-complement reference strand' )
    parser.add_option( '-F', '--offrate', dest='offrate', help='Override the offrate of the index to n' )
    parser.add_option( '-S', '--seed', dest='seed', help='Seed for pseudo-random number generator' )
    parser.add_option( '-8', '--snpphred', dest='snpphred', help='SNP penalty on Phred scale' )
    parser.add_option( '-6', '--snpfrac', dest='snpfrac', help='Fraction of sites expected to be SNP sites' )
    parser.add_option( '-7', '--keepends', dest='keepends', help='Keep extreme-end nucleotides and qualities' )
    parser.add_option( '-d', '--dbkey', dest='dbkey', help='Dbkey of reference genome' )
    parser.add_option( '-C', '--params', dest='params', help='Whether to use default or specified parameters' )
    parser.add_option( '-u', '--iauto_b', dest='iauto_b', help='Automatic or specified behavior' )
    parser.add_option( '-K', '--ipacked', dest='ipacked', help='Whether or not to use a packed representation for DNA strings' )
    parser.add_option( '-Q', '--ibmax', dest='ibmax', help='Maximum number of suffixes allowed in a block' )
    parser.add_option( '-Y', '--ibmaxdivn', dest='ibmaxdivn', help='Maximum number of suffixes allowed in a block as a fraction of the length of the reference' )
    parser.add_option( '-D', '--idcv', dest='idcv', help='The period for the difference-cover sample' )
    parser.add_option( '-U', '--inodc', dest='inodc', help='Whether or not to disable the use of the difference-cover sample' )
    parser.add_option( '-y', '--inoref', dest='inoref', help='Whether or not to build the part of the reference index used only in paired-end alignment' )
    parser.add_option( '-z', '--ioffrate', dest='ioffrate', help='How many rows get marked during annotation of some or all of the Burrows-Wheeler rows' )
    parser.add_option( '-W', '--iftab', dest='iftab', help='The size of the lookup table used to calculate an initial Burrows-Wheeler range with respect to the first n characters of the query' )
    parser.add_option( '-X', '--intoa', dest='intoa', help='Whether or not to convert Ns in the reference sequence to As' )
    parser.add_option( '-N', '--iendian', dest='iendian', help='Endianness to use when serializing integers to the index file' )
    parser.add_option( '-Z', '--iseed', dest='iseed', help='Seed for the pseudorandom number generator' )
    parser.add_option( '-c', '--icutoff', dest='icutoff', help='Number of first bases of the reference sequence to index' )
    parser.add_option( '-x', '--indexSettings', dest='index_settings', help='Whether or not indexing options are to be set' )
    parser.add_option( '-H', '--suppressHeader', dest='suppressHeader', help='Suppress header' )
    (options, args) = parser.parse_args()
    # make temp directory for placement of indices and copy reference file there if necessary
    tmp_index_dir = tempfile.mkdtemp()
    # get type of data (solid or solexa)
    if options.dataType == 'solid':
        colorspace = '-C'
    else:
        colorspace = ''
    # index if necessary
    if options.genomeSource == 'cHistory' or options.genomeSource == 'xHistory':
        # set up commands
        if options.index_settings =='cIndexPreSet' or options.index_settings == 'xIndexPreSet':
            indexing_cmds = '%s' % colorspace
        else:
            try:
                if options.iauto_b == 'set':
                    iauto_b = '--noauto'
                else:
                    iauto_b = ''
                if options.ipacked == 'packed':
                    ipacked = '--packed'
                else:
                    ipacked = ''
                if options.ibmax != 'None' and int( options.ibmax ) >= 1:
                    ibmax = '--bmax %s' % options.ibmax 
                else:
                    ibmax = ''
                if options.ibmaxdivn != 'None' and int( options.ibmaxdivn ) >= 0:
                    ibmaxdivn = '--bmaxdivn %s' % options.ibmaxdivn
                else:
                    ibmaxdivn = ''
                if options.idcv != 'None' and int( options.idcv ) > 0:
                    idcv = '--dcv %s' % options.idcv
                else:
                    idcv = ''
                if options.inodc == 'nodc':
                    inodc = '--nodc'
                else:
                    inodc = ''
                if options.inoref == 'noref':
                    inoref = '--noref'
                else:
                    inoref = ''
                if options.iftab != 'None' and int( options.iftab ) >= 0:
                    iftab = '--ftabchars %s' % options.iftab
                else:
                    iftab = ''
                if options.intoa == 'yes':
                    intoa = '--ntoa'
                else:
                    intoa = ''
                if options.iendian == 'big':
                    iendian = '--big'
                else:
                    iendian = '--little'
                if int( options.iseed ) > 0:
                    iseed = '--seed %s' % options.iseed
                else:
                    iseed = ''
                if int( options.icutoff ) > 0:
                    icutoff = '--cutoff %s' % options.icutoff
                else:
                    icutoff = ''
                indexing_cmds = '%s %s %s %s %s %s %s --offrate %s %s %s %s %s %s %s' % \
                                ( iauto_b, ipacked, ibmax, ibmaxdivn, idcv, inodc, 
                                  inoref, options.ioffrate, iftab, intoa, iendian, 
                                  iseed, icutoff, colorspace )
            except ValueError:
                indexing_cmds = ''
        try:
            shutil.copy( options.ref, tmp_index_dir )
        except Exception, e:
            stop_err( 'Error creating temp directory for indexing purposes\n' + str( e ) )
        options.ref = os.path.join( tmp_index_dir, os.path.split( options.ref )[1] )
        cmd1 = 'bowtie-build %s -f %s %s 2> /dev/null' % ( indexing_cmds, options.ref, options.ref )
        try:
            os.chdir( tmp_index_dir )
            os.system( cmd1 )
        except Exception, e:
            stop_err( 'Error indexing reference sequence\n' + str( e ) )
    # set up aligning and generate aligning command options
    # automatically set threads in both cases
    if options.suppressHeader == 'true':
        suppressHeader = '--sam-nohead'
    else:
        suppressHeader = ''
    if options.params == 'csPreSet' or options.params == 'cpPreSet' or \
            options.params == 'xsPreSet' or options.params == 'xpPreSet':
        aligning_cmds = '-p %s -S %s -q %s ' % ( options.threads, suppressHeader, colorspace )
    else:
        try:
            if options.skip != 'None' and int( options.skip ) > 0:
                skip = '-s %s' % options.skip
            else:
                skip = ''
            if int( options.alignLimit ) >= 0:
                alignLimit = '-u %s' % options.alignLimit
            else:
                alignLimit = ''
            if int( options.trimH ) > 0:
                trimH = '-5 %s' % options.trimH
            else:
                trimH = ''
            if int( options.trimL ) > 0:
                trimL = '-3 %s' % options.trimL
            else:
                trimL = ''
            if options.mismatchSeed == '0' or options.mismatchSeed == '1' or options.mismatchSeed == '2' or options.mismatchSeed == '3':
                mismatchSeed = '-n %s' % options.mismatchSeed
            else:
                mismatchSeed = ''
            if int( options.mismatchQual ) >= 0:
                mismatchQual = '-e %s' % options.mismatchQual
            else:
                mismatchQual = ''
            if int( options.seedLen ) >= 5:
                seedLen = '-l %s' % options.seedLen
            else:
                seedLen = ''
            if options.rounding == 'noRound':
                rounding = '--nomaqround'
            else:
                rounding = ''
            if options.maqSoapAlign != '-1':
                maqSoapAlign = '-v %s' % options.maqSoapAlign
            else:
                maqSoapAlign = ''
            if options.minInsert != 'None' and int( options.minInsert ) > 0:
                minInsert = '-I %s' % options.minInsert
            else:
                minInsert = ''
            if options.maxInsert != 'None' and int( options.maxInsert ) > 0:
                maxInsert = '-X %s' % options.maxInsert
            else:
                maxInsert = ''
            if options.mateOrient != 'None':
                mateOrient = '--%s' % options.mateOrient
            else:
                mateOrient = ''
            if options.maxAlignAttempt != 'None' and int( options.maxAlignAttempt ) >= 0:
                maxAlignAttempt = '--pairtries %s' % options.maxAlignAttempt
            else:
                maxAlignAttempt = ''
            if options.forwardAlign == 'noForward':
                forwardAlign = '--nofw'
            else:
                forwardAlign = ''
            if options.reverseAlign == 'noReverse':
                reverseAlign = '--norc'
            else:
                reverseAlign = ''
            if options.maxBacktracks != 'None' and int( options.maxBacktracks ) > 0 and \
                    ( options.mismatchSeed == '2' or options.mismatchSeed == '3' ):
                maxBacktracks = '--maxbts %s' % options.maxBacktracks
            else:
                maxBacktracks = ''
            if options.tryHard == 'doTryHard':
                tryHard = '-y'
            else:
                tryHard = ''
            if options.valAlign != 'None' and int( options.valAlign ) >= 0:
                valAlign = '-k %s' % options.valAlign
            else:
                valAlign = ''
            if options.allValAligns == 'doAllValAligns':
                allValAligns = '-a'
            else:
                allValAligns = ''
            if options.suppressAlign != 'None' and int( options.suppressAlign ) >= 0:
                suppressAlign = '-m %s' % options.suppressAlign
            else:
                suppressAlign = ''
            if options.best == 'csDoBest' or options.best == 'cpDoBest' or \
                    options.best == 'xsDoBest' or options.best == 'xpDoBest':
                best = '--best'
            else:
                best = ''
            if options.strata == 'doStrata':
                strata = '--strata'
            else:
                strata = ''
            if options.offrate != 'None' and int( options.offrate ) >= 0:
                offrate = '-o %s' % options.offrate
            else:
                offrate = ''
            if options.seed != 'None' and int( options.seed ) >= 0:
                seed = '--seed %s' % options.seed
            else:
                seed = ''
            if options.snpphred != 'None' and int( options.snpphred ) >= 0:
                snpphred = '--snpphred %s' % options.snpphred
            else:
                snpphred = ''
            if options.snpfrac != 'None' and float( options.snpfrac ) >= 0:
                snpfrac = '--snpfrac %s' % options.snpfrac
            else:
                snpfrac = ''
            if options.keepends != 'None' and options.keepends == 'doKeepends':
                keepends = '--col-keepends'
            else:
                keepends = ''
            aligning_cmds = '%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s ' \
                            '%s %s %s %s %s %s %s %s %s %s %s -p %s -S %s -q' % \
                            ( skip, alignLimit, trimH, trimL, mismatchSeed, mismatchQual, 
                              seedLen, rounding, maqSoapAlign, minInsert, maxInsert, 
                              mateOrient, maxAlignAttempt, forwardAlign, reverseAlign, 
                              maxBacktracks, tryHard, valAlign, allValAligns, suppressAlign, 
                              best, strata, offrate, seed, colorspace, snpphred, snpfrac, 
                              keepends, options.threads, suppressHeader )
        except ValueError, e:
            stop_err( 'Something is wrong with the alignment parameters and the alignment could not be run\n' + str( e ) )
    # prepare actual aligning commands
    if options.paired == 'cPaired' or options.paired == 'xPaired':
        cmd2 = 'bowtie %s %s -1 %s -2 %s > %s 2> /dev/null' % ( aligning_cmds, options.ref, options.input1, options.input2, options.output ) 
    else:
        cmd2 = 'bowtie %s %s %s > %s 2> /dev/null' % ( aligning_cmds, options.ref, options.input1, options.output ) 
    # align
    try:
        os.system( cmd2 )
    except Exception, e:
        stop_err( 'Error aligning sequence\n' + str( e ) )
    # clean up temp dir
    if os.path.exists( tmp_index_dir ):
        shutil.rmtree( tmp_index_dir )

if __name__=="__main__": __main__()
