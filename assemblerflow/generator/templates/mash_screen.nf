// creates two channels for each approach
Channel
    .value("/home/data/patlas.msh")
    .into { refSketchChannel }
}

// process to run mashScreen and sort the output into
// sortedMashScreenResults_{sampleId}.txt
process mashScreen {

    tag { "running mash screen for sample: " + sample }

    input:
    set sample, file(reads) from {{ input_channel }}
    val refSketch from refSketchChannel

    output:
    set sample, file("sortedMashScreenResults_${sample}.txt") into mashScreenResults

    """
    mash screen -i ${params.identity} -v ${params.pValue} -p \
    ${params.threads} ${winnerVar} ${refSketch} ${reads} > mashScreenResults_${sample}.txt
    sort -gr mashScreenResults_${sample}.txt > sortedMashScreenResults_${sample}.txt
    """
}

// process to parse the output to json format
process mashOutputJson {

    tag { "dumping json file from: " + mashtxt }

    input:
    set sample, file(mashtxt) from mashScreenResults

    output:
    file "sortedMashScreenResults_${sample}.json" into {{ output_channel }}

    script:
    template "mashscreen2json.py"
}

{{ forks }}