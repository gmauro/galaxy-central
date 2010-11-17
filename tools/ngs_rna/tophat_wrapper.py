#!/usr/bin/env python

import optparse, os, shutil, subprocess, sys, tempfile, fileinput

def stop_err( msg ):
    sys.stderr.write( "%s\n" % msg )
    sys.exit()

def __main__():
    #Parse Command Line
    parser = optparse.OptionParser()
    parser.add_option( '-p', '--num-threads', dest='num_threads', help='Use this many threads to align reads. The default is 1.' )
    parser.add_option( '-J', '--junctions-output', dest='junctions_output_file', help='Junctions output file; formate is BED.' )
    parser.add_option( '-H', '--hits-output', dest='accepted_hits_output_file', help='Accepted hits output file; formate is BAM.' )
    parser.add_option( '', '--own-file', dest='own_file', help='' )
    parser.add_option( '-D', '--indexes-path', dest='index_path', help='Indexes directory; location of .ebwt and .fa files.' )
    parser.add_option( '-r', '--mate-inner-dist', dest='mate_inner_dist', help='This is the expected (mean) inner distance between mate pairs. \
                                                                                For, example, for paired end runs with fragments selected at 300bp, \
                                                                                where each end is 50bp, you should set -r to be 200. There is no default, \
                                                                                and this parameter is required for paired end runs.')
    parser.add_option( '', '--mate-std-dev', dest='mate_std_dev', help='Standard deviation of distribution on inner distances between male pairs.' )
    parser.add_option( '-a', '--min-anchor-length', dest='min_anchor_length', 
                        help='The "anchor length". TopHat will report junctions spanned by reads with at least this many bases on each side of the junction.' )
    parser.add_option( '-m', '--splice-mismatches', dest='splice_mismatches', help='The maximum number of mismatches that can appear in the anchor region of a spliced alignment.' )
    parser.add_option( '-i', '--min-intron-length', dest='min_intron_length', 
                        help='The minimum intron length. TopHat will ignore donor/acceptor pairs closer than this many bases apart.' )
    parser.add_option( '-I', '--max-intron-length', dest='max_intron_length', 
                        help='The maximum intron length. When searching for junctions ab initio, TopHat will ignore donor/acceptor pairs farther than this many bases apart, except when such a pair is supported by a split segment alignment of a long read.' )
    parser.add_option( '-F', '--junction_filter', dest='junction_filter', help='Filter out junctions supported by too few alignments (number of reads divided by average depth of coverage)' )
    parser.add_option( '-g', '--max_multihits', dest='max_multihits', help='Maximum number of alignments to be allowed' )
    parser.add_option( '', '--seg-mismatches', dest='seg_mismatches', help='Number of mismatches allowed in each segment alignment for reads mapped independently' )
    parser.add_option( '', '--seg-length', dest='seg_length', help='Minimum length of read segments' )

    # Options for supplying own junctions
    parser.add_option( '-G', '--GTF', dest='gene_model_annotations', help='Supply TopHat with a list of gene model annotations. \
                                                                           TopHat will use the exon records in this file to build \
                                                                           a set of known splice junctions for each gene, and will \
                                                                           attempt to align reads to these junctions even if they \
                                                                           would not normally be covered by the initial mapping.')
    parser.add_option( '-j', '--raw-juncs', dest='raw_juncs', help='Supply TopHat with a list of raw junctions. Junctions are \
                                                                    specified one per line, in a tab-delimited format. Records \
                                                                    look like: <chrom> <left> <right> <+/-> left and right are \
                                                                    zero-based coordinates, and specify the last character of the \
                                                                    left sequenced to be spliced to the first character of the right \
                                                                    sequence, inclusive.')
    parser.add_option( '', '--no-novel-juncs', action="store_true", dest='no_novel_juncs', help="Only look for junctions indicated in the \
                                                                                            supplied GFF file. (ignored without -G)")
    # Types of search.
    parser.add_option( '', '--microexon-search', action="store_true", dest='microexon_search', help='With this option, the pipeline will attempt to find alignments incident to microexons. Works only for reads 50bp or longer.')
    parser.add_option( '', '--closure-search', action="store_true", dest='closure_search', help='Enables the mate pair closure-based search for junctions. Closure-based search should only be used when the expected inner distance between mates is small (<= 50bp)')
    parser.add_option( '', '--no-closure-search', action="store_false", dest='closure_search' )
    parser.add_option( '', '--coverage-search', action="store_true", dest='coverage_search', help='Enables the coverage based search for junctions. Use when coverage search is disabled by default (such as for reads 75bp or longer), for maximum sensitivity.')
    parser.add_option( '', '--no-coverage-search', action="store_false", dest='coverage_search' )
    parser.add_option( '', '--min-segment-intron', dest='min_segment_intron', help='Minimum intron length that may be found during split-segment search' )
    parser.add_option( '', '--max-segment-intron', dest='max_segment_intron', help='Maximum intron length that may be found during split-segment search' )
    parser.add_option( '', '--min-closure-exon', dest='min_closure_exon', help='Minimum length for exonic hops in potential splice graph' )
    parser.add_option( '', '--min-closure-intron', dest='min_closure_intron', help='Minimum intron length that may be found during closure search' )
    parser.add_option( '', '--max-closure-intron', dest='max_closure_intron', help='Maximum intron length that may be found during closure search' )
    parser.add_option( '', '--min-coverage-intron', dest='min_coverage_intron', help='Minimum intron length that may be found during coverage search' )
    parser.add_option( '', '--max-coverage-intron', dest='max_coverage_intron', help='Maximum intron length that may be found during coverage search' )

    # Wrapper options.
    parser.add_option( '-1', '--input1', dest='input1', help='The (forward or single-end) reads file in Sanger FASTQ format' )
    parser.add_option( '-2', '--input2', dest='input2', help='The reverse reads file in Sanger FASTQ format' )
    parser.add_option( '', '--single-paired', dest='single_paired', help='' )
    parser.add_option( '', '--settings', dest='settings', help='' )

    (options, args) = parser.parse_args()

    # Creat bowtie index if necessary.
    tmp_index_dir = tempfile.mkdtemp()
    if options.own_file:
        index_path = os.path.join( tmp_index_dir, os.path.split( options.own_file )[1] )
        cmd_index = 'bowtie-build -f %s %s' % ( options.own_file, index_path )
        try:
            tmp = tempfile.NamedTemporaryFile( dir=tmp_index_dir ).name
            tmp_stderr = open( tmp, 'wb' )
            proc = subprocess.Popen( args=cmd_index, shell=True, cwd=tmp_index_dir, stderr=tmp_stderr.fileno() )
            returncode = proc.wait()
            tmp_stderr.close()
            # get stderr, allowing for case where it's very large
            tmp_stderr = open( tmp, 'rb' )
            stderr = ''
            buffsize = 1048576
            try:
                while True:
                    stderr += tmp_stderr.read( buffsize )
                    if not stderr or len( stderr ) % buffsize != 0:
                        break
            except OverflowError:
                pass
            tmp_stderr.close()
            if returncode != 0:
                raise Exception, stderr
        except Exception, e:
            if os.path.exists( tmp_index_dir ):
                shutil.rmtree( tmp_index_dir )
            stop_err( 'Error indexing reference sequence\n' + str( e ) )
    else:
        index_path = options.index_path

    # Build tophat command.
    tmp_output_dir = tempfile.mkdtemp()
    cmd = 'tophat -o %s %s %s %s'
    reads = options.input1
    if options.input2:
        reads += ' ' + options.input2
    opts = '-p %s' % options.num_threads
    if options.single_paired == 'paired':
        opts += ' -r %s' % options.mate_inner_dist
    if options.settings == 'preSet':
        cmd = cmd % ( tmp_output_dir, opts, index_path, reads )
    else:
        try:
            if int( options.min_anchor_length ) >= 3:
                opts += ' -a %s' % options.min_anchor_length
            else:
                raise Exception, 'Minimum anchor length must be 3 or greater'
            opts += ' -m %s' % options.splice_mismatches
            opts += ' -i %s' % options.min_intron_length
            opts += ' -I %s' % options.max_intron_length
            if float( options.junction_filter ) != 0.0:
                opts += ' -F %s' % options.junction_filter
            opts += ' -g %s' % options.max_multihits
            # Custom junctions options.
            if options.gene_model_annotations:
                opts += ' -G %s' % options.gene_model_annotations
            if options.raw_juncs:
                opts += ' -j %s' % options.raw_juncs
            if options.no_novel_juncs:
                opts += ' --no-novel-juncs'

            # Search type options.
            if options.coverage_search:
                opts += ' --coverage-search --min-coverage-intron %s --max-coverage-intron %s' % ( options.min_coverage_intron, options.max_coverage_intron )
            else:
                opts += ' --no-coverage-search'
            if options.closure_search:
                opts += ' --closure-search --min-closure-exon %s --min-closure-intron %s --max-closure-intron %s'  % ( options.min_closure_exon, options.min_closure_intron, options.max_closure_intron ) 
            else:
                opts += ' --no-closure-search'
            if options.microexon_search:
                opts += ' --microexon-search'
            if options.single_paired == 'paired':
                opts += ' --mate-std-dev %s' % options.mate_std_dev
            if options.seg_mismatches:
                opts += ' --segment-mismatches %d' % int(options.seg_mismatches)
            if options.seg_length:
                opts += ' --segment-length %d' % int(options.seg_length)
            if options.min_segment_intron:
                opts += ' --min-segment-intron %d' % int(options.min_segment_intron)
            if options.max_segment_intron:
                opts += ' --max-segment-intron %d' % int(options.max_segment_intron)
            cmd = cmd % ( tmp_output_dir, opts, index_path, reads )
        except Exception, e:
            # Clean up temp dirs
            if os.path.exists( tmp_index_dir ):
                shutil.rmtree( tmp_index_dir )
            if os.path.exists( tmp_output_dir ):
                shutil.rmtree( tmp_output_dir )
            stop_err( 'Something is wrong with the alignment parameters and the alignment could not be run\n' + str( e ) )
    print cmd

    # Run
    try:
        tmp_out = tempfile.NamedTemporaryFile( dir=tmp_output_dir ).name
        tmp_stdout = open( tmp_out, 'wb' )
        tmp_err = tempfile.NamedTemporaryFile( dir=tmp_output_dir ).name
        tmp_stderr = open( tmp_err, 'wb' )
        proc = subprocess.Popen( args=cmd, shell=True, cwd=tmp_output_dir, stdout=tmp_stdout, stderr=tmp_stderr )
        returncode = proc.wait()
        tmp_stderr.close()
        # get stderr, allowing for case where it's very large
        tmp_stderr = open( tmp_err, 'rb' )
        stderr = ''
        buffsize = 1048576
        try:
            while True:
                stderr += tmp_stderr.read( buffsize )
                if not stderr or len( stderr ) % buffsize != 0:
                    break
        except OverflowError:
            pass
        tmp_stdout.close()
        tmp_stderr.close()
        if returncode != 0:
            raise Exception, stderr

        # TODO: look for errors in program output.

        # Copy output files from tmp directory to specified files.
        shutil.copyfile( os.path.join( tmp_output_dir, "junctions.bed" ), options.junctions_output_file )
        shutil.copyfile( os.path.join( tmp_output_dir, "accepted_hits.bam" ), options.accepted_hits_output_file )
    except Exception, e:
        stop_err( 'Error in tophat:\n' + str( e ) ) 
    finally:
        # Clean up temp dirs
        if os.path.exists( tmp_index_dir ):
            shutil.rmtree( tmp_index_dir )
        if os.path.exists( tmp_output_dir ):
            shutil.rmtree( tmp_output_dir )

if __name__=="__main__": __main__()
