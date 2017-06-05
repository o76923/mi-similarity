# Mihalcea Similarity Calculator
This container is used to calculate semantic similarity based on Mihalcea's
algorithm for short text similarity as described in Mihalcea, Corley, & 
Strapparava (2006). Some slight modifications have been made to this 
instantiation of the algorithm as described in Larsen & Bong (2016).

## Running the Tool
In order to run the tool, type the following into your terminal

```bash
docker run -it -v /local/data/path/:/app/data -e CONFIG_FILE=config.yml o76923/mi-similarity
```
Where `/local/data/path/` is the path on your local system that contains the 
source information and `config.yml` is the configuration file in that directory
containing which tasks should be performed as well as their settings.

## Directory Structure
The path on your local machine should contain the following
1. A configuration file
1. An information content file
1. The texts to be compared

## Configuration File
The configuration file specifies the parameters that will tweak how the tool 
behaves. A sample configuration file is provided in `/app/conf/config.yml`.
The sections of it are as follows

### Tasks
There is presently only one task that can be performed with this tool:
"calculate_similarity".

#### calculate_similarity
The calculate_similarity task is used to generate semantic similarity scores 
between short texts. A sample calculate_similarity task is included below, 
followed by an explanation of the options available.

```yaml
  - type: calculate_similarity
    from:
      files:
        - input/def.txt
      pairs: all
      headers: true
      numbered: true
    options:
      batch_size: 100
    output:
      format: H5
      file_name: def.h5
      ds_name: mi
```

<dl>
  <dt>files</dt>
  <dd>A list of files that contain the short texts to be compared.</dd>
  <dt>pairs</dt>
  <dd>Which pairs of short texts should be compared to one another? At the
    moment, "all" is the only option supported which compares each text to
    every other text.</dd>
  <dt>headers</dt>
  <dd>Do your files contain a header row that should be skipped?</dd>
  <dt>numbered</dt>
  <dd>Do the texts have IDs assigned to them already?</dd>
  <dt>format</dt>
  <dd>What format should the similarity scores be written to? At the moment,
    only "H5" is available which saves the output in the HDF5 file format.</dd>
  <dt>file_name</dt>
  <dd>The name of the similarity file. It will be placed in the 
    `/app/data/output` directory.</dd>
  <dt>ds_name</dt>
  <dd>If the format is "H5", you can specify the name of the data source. This
    name will be used in both the sims and vector groups.</dd>
</dl>

### Options
Options specifies global options that will apply to all tasks run. At this
time, only one option is available.
<dl>
  <dt>cores</dt>
  <dd>The maximum number of processor cores that can be used at any given time.
    Note that this is based on how many threads that this tool will create on
    its own. It is possible, due to the use of certain math libraries, that
    more than this number of cores will be used.</dd>
</dl>

## Information Content File
The Mi algorithm requires that there be a .ic file which stores information on
the inverse document frequency of words based on a corpus. These freqeuncies
are used in the Wu & Palmer; Lin; and Jiang & Conrath wordnet similarity 
components.

This file is expected to be located in `/app/data/bnc.ic` which should be in
the base directory of `/local/data/path/`.

The source data can be downloaded from the page for the [WordNet::Similarity](http://www.d.umn.edu/~tpederse/Data/WordNet-InfoContent-3.0.tar.gz) 
perl package.

Based on this sorce data, you will need to convert it from a .dat file with raw
counts to a .ic file that contains the inverse document frequency. Instructions
for this process are coming soon.

## Texts to be Compared
The texts to be compared are the short texts that you wish to have compared to 
one another. Similarity scores will be generated between texts with one ID and
texts with another ID.