#!/usr/bin/env python2.4


"""
histogram_gnuplot.py <datafile> <xtic column> <column_list> <title> <ylabel> <yrange_min> <yrange_max> <grath_file>
a generic histogram builder based on gnuplot backend

   data_file    - tab delimited file with data
   xtic_column  - column containing labels for x ticks [integer, 0 means no ticks]
   column_list  - comma separated list of columns to plot
   title        - title for the entire histrogram
   ylabel       - y axis label
   yrange_max   - minimal value at the y axis (integer)
   yrange_max   - maximal value at the y_axis (integer) 
                  to set yrange to auto assign 0 to yrange_mmin and yrange_max
   graph_file   - file to write histogram image to
   pdf_size     - as X,Y pair in inches (e.g., 11,8 or 8,11 etc.)
   
   
   This tool required gnuplot and gnuplot.py

anton nekrutenko | anton@bx.psu.edu

"""


from Numeric import *
import Gnuplot, Gnuplot.funcutils
import sys, string, tempfile, os

def stop_err(msg):
    sys.stderr.write(msg)
    sys.exit()

def main(tmpFileName):
    skipped_lines_count = 0
    skipped_lines_index = []
    gf = open(tmpFileName, 'w')
    
    
    try:
        in_file   = open( sys.argv[1], 'r' )
        xtic      = int( sys.argv[2] )
        col_list  = string.split( sys.argv[3],"," )
        title     = 'set title "' + sys.argv[4] + '"'
        ylabel    = 'set ylabel "' + sys.argv[5] + '"'
        ymin      = sys.argv[6]
        ymax      = sys.argv[7]
        img_file  = sys.argv[8]
        pdf_size  = sys.argv[9]
    except:
        stop_err("Check arguments\n")
        
    try:
        int( col_list[0] )
    except:
        stop_err('You forgot to set columns for plotting\n')    
    
       
    for i, line in enumerate( in_file ):
        valid = True
        line = line.rstrip('\r\n')
        if line and not line.startswith( '#' ):
            row = []
            try:
                fields = line.split( '\t' )
                for col in col_list:
                    row.append( str( float( fields[int(col)-1] ) ) )
                    
            except:
                valid = False
                skipped_lines_count += 1
                skipped_lines_index.append(i)
                    
        else:
            valid = False
            skipped_lines_count += 1
            skipped_lines_index.append(i)
            
        if valid and xtic > 0:
            row.append( fields[xtic-1] )
        elif valid and xtic == 0:
            row.append( str( i ) )    
            
        if valid:
            gf.write( '\t'.join( row ) )
            gf.write( '\n' )  
             
    if skipped_lines_count < i:
        
        #prepare 'using' clause of plot statement
        
        g_plot_command = ' ';
        
        #set the first column
        if xtic > 0:
            g_plot_command = "'%s' using 1:xticlabels(%s) ti 'Column %s', " % ( tmpFileName, str( len( row ) ), col_list[0] )
            #g_plot_command = "'%s' using 1:xticlabels(%s), " % ( tmpFileName, str( len( row ) ) )
        else:
            g_plot_command = "'%s' using 1, " % ( tmpFileName )
        
        #set subsequent columns
        
        for i in range(1,len(col_list)):
            g_plot_command += "'%s' using %s t 'Column %s', " % ( tmpFileName, str(i+1), col_list[i] )
            #g_plot_command += "'%s' using %s, " % ( tmpFileName, str(i+1) )
        
        g_plot_command = g_plot_command.rstrip(', ')
        
        yrange = 'set yrange [' + ymin + ":" + ymax + ']'
                    
        try:
            g = Gnuplot.Gnuplot()
            g('reset')
            g('set boxwidth 0.9 absolute')
            g('set style fill  solid 1.00 border -1')
            g('set style histogram clustered gap 5 title  offset character 0, 0, 0')
            g('set xtics border in scale 1,0.5 nomirror rotate by 90 offset character 0, 0, 0')
            g('set key invert reverse Left outside')
            if xtic == 0:  g('unset xtics')
            g(title) 
            g(ylabel)
            g_term = 'set terminal pdf size ' + pdf_size
            g(g_term)
            g_out = 'set output "' + img_file + '"'
            if ymin != ymax:
                g(yrange)
            g(g_out)
            g('set style data histograms')
            g.plot(g_plot_command)
        except:
            stop_err("Gnuplot error: Data cannot be plotted")
    else:
        sys.stderr.write('Columns %s of your dataset do not contain valid numeric data' %sys.argv[3] )
        
    if skipped_lines_count > 0:
        sys.stderr.write('You dataset contains %d invalid lines starting with line#%d\n' % ( skipped_lines_count, skipped_lines_index[0] ) )
    

if __name__ == "__main__":
    gp_data_file = tempfile.NamedTemporaryFile('w')
    #gp_f, gp_data_file = tempfile.mkstemp(suffix="gp", text=True)
    main(gp_data_file.name)
    
