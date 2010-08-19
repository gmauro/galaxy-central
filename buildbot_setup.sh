#!/bin/sh

cd `dirname $0`

: ${HOSTTYPE:=`uname -m`}

# link to HYPHY is arch-dependent
case "$OSTYPE" in
    linux-gnu)
        kernel=`uname -r | cut -f1,2 -d.`
        HYPHY="/galaxy/software/linux$kernel-$HOSTTYPE/hyphy"
        ;;
    darwin*)
        this_minor=`uname -r | awk -F. '{print ($1-4)}'`
        machine=`machine`
        for minor in `jot - 3 $this_minor 1`; do
            HYPHY="/galaxy/software/macosx10.$minor-$machine/hyphy"
            [ -d "$HYPHY" ] && break
        done
        [ ! -d "$HYPHY" ] && unset HYPHY
        ;;
    solaris2.10)
        HYPHY="/galaxy/software/linux2.6-x86_64/hyphy"
        ;;
esac

LINKS="
/galaxy/data/location/add_scores.loc
/galaxy/data/location/alignseq.loc
/galaxy/data/annotation_profiler
/galaxy/data/annotation_profiler/annotation_profiler.loc
/galaxy/data/annotation_profiler/annotation_profiler_options.xml
/galaxy/data/annotation_profiler/annotation_profiler_valid_builds.txt
/galaxy/data/location/binned_scores.loc
/galaxy/data/location/blastdb.loc
/galaxy/data/location/bowtie_indices.loc
/galaxy/data/location/bowtie_indices_color.loc
/galaxy/data/location/bwa_index.loc
/galaxy/data/location/bfast_indexes.loc
/galaxy/data/location/codingSnps.loc
/galaxy/data/location/encode_datasets.loc
/galaxy/home/universe/encode_feature_partitions
/galaxy/data/location/lastz_seqs.loc
/galaxy/data/location/liftOver.loc
/galaxy/data/location/maf_index.loc
/galaxy/data/location/maf_pairwise.loc
/galaxy/data/location/microbes/microbial_data.loc
/galaxy/data/location/perm_base_index.loc
/galaxy/data/location/perm_color_index.loc
/galaxy/data/location/phastOdds.loc
/galaxy/data/location/quality_scores.loc
/galaxy/data/location/regions.loc
/galaxy/data/location/sam_fa_indices.loc
/galaxy/data/taxonomy
/galaxy/data/location/twobit.loc
"

SAMPLES="
datatypes_conf.xml.sample
universe_wsgi.ini.sample
tool_data_table_conf.xml.sample
tool-data/shared/ucsc/builds.txt.sample
"

DIRS="
database
database/files
database/tmp
database/compiled_templates
database/job_working_directory
database/import
database/pbs
"

for link in $LINKS; do
    echo "Linking $link"
    rm -f tool-data/`basename $link`
    ln -sf $link tool-data
done

if [ -d "$HYPHY" ]; then
    echo "Linking $HYPHY"
    rm -f tool-data/HYPHY
    ln -sf $HYPHY tool-data/HYPHY
fi

for sample in $SAMPLES; do
    file=`echo $sample | sed -e 's/\.sample$//'`
    echo "Copying $sample to $file"
    cp $sample $file
done

for dir in $DIRS; do
    if [ ! -d $dir ]; then
        echo "Creating $dir"
        mkdir $dir
    fi
done

python ./scripts/fetch_eggs.py all
