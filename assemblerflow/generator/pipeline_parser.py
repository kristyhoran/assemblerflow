import logging

logger = logging.getLogger("main.{}".format(__name__))

# Set the tokens used for the main syntax
# Token signaling the start of a fork
FORK_TOKEN = "("
# Token separating different lanes from a fork
LANE_TOKEN = "|"
# Token that closes a fork
CLOSE_TOKEN = ")"


def parse_pipeline(pipeline_str):
    """Parses a pipeline string into a dictionary with the connections between
    process

    Parameters
    ----------
    pipeline_str : str
        String with the definition of the pipeline, e.g.::
            'processA processB processC(ProcessD | ProcessE)'

    Returns
    -------
    pipeline_links : list

    """

    #TODO: Add string check here

    pipeline_links = []
    lane = 1

    # Get number of forks in the pipeline
    nforks = pipeline_str.count(FORK_TOKEN)
    logger.debug("Found {} fork(s)".format(nforks))

    # If there are no forks, connect the pipeline as purely linear
    if not nforks:
        pipeline_links.extend(linear_connection(pipeline_str.split(), lane))
        return pipeline_links

    for i in range(nforks):

        # Split the pipeline at each fork start position. fields[-1] will
        # hold the process after the fork. fields[-2] will hold the processes
        # before the fork.
        fields = pipeline_str.split(FORK_TOKEN, i + 1)

        # Get the processes before the fork. This may be empty when the
        # fork is at the beginning of the pipeline.
        previous_process = fields[-2].split()
        # Get lanes after the fork
        next_lanes = get_lanes(fields[-1])
        # Get the immediate targets of the fork
        fork_sink = [x[0] for x in next_lanes]

        # The first fork is a special case, where the processes before AND
        # after the fork (until the start of another fork) are added to
        # the ``pipeline_links`` variable. Otherwise, only the processes
        # after the fork will be added
        if i == 0:
            # If there are no previous process, the fork is at the beginning
            # of the pipeline string. In this case, inject the special
            # "init" process.
            if not previous_process:
                previous_process = ["init"]

            # Add the linear modules before the fork
            pipeline_links.extend(
                linear_connection(previous_process, lane))

        fork_source = previous_process[-1]
        # Add the forking modules
        pipeline_links.extend(
            fork_connection(fork_source, fork_sink, lane))
        # Add the linear connections in the subsequent lanes
        pipeline_links.extend(
            linear_lane_connection(next_lanes, lane))

        lane += len(fork_sink)

    return pipeline_links


def get_lanes(lanes_str):
    """From a raw pipeline string, get a list of lanes from the start
    of the current fork.

    When the pipeline is being parsed, it will be split at every fork
    position. The string at the right of the fork position will be provided
    to this function. It's job is to retrieve the lanes that result
    from that fork, ignoring any nested forks.

    Parameters
    ----------
    lanes_str : str
        Pipeline string after a fork split

    Returns
    -------
    lanes : list
        List of lists, with the list of processes for each lane

    """

    # Temporarily stores the lanes string after removal of nested forks
    parsed_lanes = ""
    # Flag used to determined whether the cursor is inside or outside the
    # right fork
    infork = 0

    for i in lanes_str:

        # Nested fork started
        if i == FORK_TOKEN:
            infork += 1
        # Nested fork stopped
        if i == CLOSE_TOKEN:
            infork -= 1

        # Save only when in the right fork
        if infork == 0:
            # Ignore forking syntax tokens
            if i not in [FORK_TOKEN, CLOSE_TOKEN]:
                parsed_lanes += i

    return [x.split() for x in parsed_lanes.split(LANE_TOKEN)]


def linear_connection(plist, lane):
    """Connects a linear list of processes into a list of dictionaries

    Parameters
    ----------
    plist : list
        List with process names. This list should contain at least two entries.
    lane : int
        Corresponding lane of the processes

    Returns
    -------
    res : list
        List of dictionaries with the links between processes
    """

    res = []
    previous = None

    for p in plist:
        # Skip first process
        if not previous:
            previous = p
            continue

        res.append({
            "input": previous,
            "output": p,
            "lane": lane
        })

    return res


def fork_connection(source, sink, lane):
    """Makes the connection between a process and the first processes in the
    lanes to wich it forks.

    The ``lane`` argument should correspond to the lane of the source process.
    For each lane in ``sink``, the lane counter will increase.

    Parameters
    ----------
    source : str
        Name of the process that is forking
    sink : list
        List of the processes where the source will fork to. Each element
        corresponds to the start of a lane.
    lane : int
        Lane of the source process

    Returns
    -------
    res : list
        List of dictionaries with the links between processes
    """

    res = []
    # Increase the lane counter for the first lane
    lane += 1

    for p in sink:
        res.append({
            "input": source,
            "output": p,
            "lane": lane
        })
        lane += 1

    return res


def linear_lane_connection(lane_list, lane):
    """

    Parameters
    ----------
    lane_list : list
        Each element should correspond to a list of processes for a given lane
    lane : int
        Lane counter before the fork start

    Returns
    -------
    res : list
        List of dictionaries with the links between processes
    """

    res = []
    # Increase the lane counter for the first lane
    lane += 1

    for l in lane_list:
        res.extend(linear_connection(l, lane))
        lane += 1

    return res