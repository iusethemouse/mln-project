import uunet.multinet as ml

def parse_language_file(language_file):
    print(f'Parsing MLN language file {language_file}')
    language = {
        'states': [],
        'parameters': [],
        'initial conditions': [],
        'rules': [],
        'views': [],
        'simOptions': []
    }
    
    language_file = open(language_file, 'r').readlines()
    
    saving_lines = False
    key = ''
    for line in language_file:
        if 'begin' in line:
            saving_lines = True
            l = line.split()[1:]
            if len(l) > 1:
                l = ' '.join(l)
            else:
                l = l[0]
            key = l
        elif 'end' in line:
            saving_lines = False

        if saving_lines and 'begin' not in line:
            language[key].append(line.strip('\n'))
            
    return language
    

def parse_mln(mln_filename):
    print(f'Parsing network configuration file {mln_filename}')
    net = ml.read(mln_filename)
    
    ### Number of actors
    actors = ml.actors(net)
    # N_actors = max(list(map(int, actors)))
    N_actors = len(actors)

    ### Number of layers
    layers = ml.layers(net)
    # N_layers = max(list(map(int, layers)))
    N_layers = len(layers)

    #### Then we extract all the edges we need from the MLN
    #### (here i check if they undirected and take them both, maybe it is best to do this check in
    #### when parsing the rules)

    edges = ml.edges(net)
    edges

    list_split_edges = [] 

    for layer in layers: 
        list_collecting_edges = [] 
        idx_list = [i for i,j in enumerate(edges['from_layer']) if j == layer]
        for i in idx_list : 
            list_collecting_edges.append((edges['from_actor'][i] , edges['to_actor'][i]) )
            if edges['dir'][i] == False: 
                list_collecting_edges.append( (edges['to_actor'][i] , edges['from_actor'][i]) )

        list_split_edges.append(list_collecting_edges)
        
    mln_data = {
        'actors': (actors, N_actors),
        'layers': (layers, N_layers),
        'edges': (edges, list_split_edges)
                }
    
    return mln_data


def parse_to_kappa(network_filename, language_filename, out_filename):
    mln_data = parse_mln(network_filename)
    language = parse_language_file(language_filename)
    
    kappa_model = ''
    kappa_model += kappa_parse_signatures(mln_data, language) + '\n\n'
    kappa_model += kappa_parse_rules(mln_data, language) + '\n'
    kappa_model += kappa_parse_variables(language) + '\n\n'
    kappa_model += kappa_parse_observables(mln_data, language) + '\n\n'
    kappa_model += kappa_parse_initial_conditions(mln_data, language)
    
    with open(out_filename, 'w') as f:
        f.write(kappa_model)

    print(f'Successfully exported model into Kappa: {out_filename}')
    

def kappa_parse_signatures(mln_data, language):
    signatures = ['/* Signatures */']
    
    states = '{' + ', '.join(language['states']) + '}'

    for actor in mln_data['actors'][0]:
        sites = []
        for j, layer in enumerate(mln_data['edges'][1]):
            for edge in layer:
                if edge[0] == actor:
                    sites.append(f'l{j+1}v{edge[1]}')
        sites = ', '.join(sites)
                                 
        kappa_signature = f'%agent: V{actor}(state{states}, {sites})'
        signatures.append(kappa_signature)
        
        
    signatures = '\n'.join(signatures)
    
    return signatures


def kappa_parse_variables(language):
    variables = ['/* Variables */']
    
    for param in language['parameters']:
        var_name, var_value = param.split('=')
        var = f"%var: '{var_name.strip()}' {var_value.strip()}"
        variables.append(var)
    variables = '\n'.join(variables)
    
    return variables


def kappa_parse_observables(mln_data, language):
    observables = ['/* Observables */']
    
    for view in language['views']:
        components = []
        for i, actor in enumerate(mln_data['actors'][0]):
            components.append(f'|V{i+1}(state{{{view}}})|')
        obs = f"%obs: '{view}' " + ' + '.join(components)
        observables.append(obs)
    
    observables = '\n'.join(observables)
    
    return observables


def kappa_parse_initial_conditions(mln_data, language):
    n = ''
    for line in language['simOptions']:
        option, value = line.split('=')
        if option.strip() == 'n':
            n = value.strip()
            break
            
    i_c = ['/* Initial conditions */',
           f'%init: {n} (']
    
    initial_states = [x.split('=') for x in language['initial conditions']]

    for i, actor in enumerate(mln_data['actors'][0]):
        sites = []
        site_labels = []
        for j, layer in enumerate(mln_data['edges'][1]):
            for edge in layer:
                if edge[0] == str(i+1):
                    # weird way to keep site labels consistent.
                    # will need a rewrite
                    if i+1 <= int(edge[1]):
                        site_label = f'{j+1}{i+1}{edge[1]}'
                    else:
                        site_label = f'{j+1}{edge[1]}{i+1}'
                        
                    sites.append(f'l{j+1}v{edge[1]}[{site_label}]')
        sites = ', '.join(sites)
        
        initial_state = ''
        for state in initial_states:
            if state[0].strip() == str(i+1):
                initial_state = state[1].strip()
                
        condition = f'V{i+1}(state{{{initial_state}}}, {sites})'
        
        # add a comma unless it's the last entry
        if i + 1 < int(mln_data['actors'][1]):
            condition += ','
        
        i_c.append(condition)
    
    i_c.append(')')
        
    i_c = '\n'.join(i_c)
    
    return i_c


def kappa_parse_rules(mln_data, language):
    kappa_rules = ['/* Rules */']
    
    rules = [x.split('@') for x in language['rules']]
    rules_organised = []
    for ruleset in rules:
        rules_organised.append({'rule': ruleset[0].strip(), 'rate': ruleset[1].strip()})

    for ruleset in rules_organised:
        if '=' not in ruleset['rule']:
            # parse rules not dependant on layers
            rule_states = [state.strip() for state in ruleset['rule'].split('->')]
            kappa_rules.append(f"'{rule_states[0]} to {rule_states[1]}'")
            for i, actor in enumerate(mln_data['actors'][0]):
                kappa_rule = f"V{i+1}(state{{{rule_states[0]}}}) -> V{i+1}(state{{{rule_states[1]}}}) @ '{ruleset['rate']}'"
                kappa_rules.append(kappa_rule)
        else:
            # parse intra-layer rules
            # requires rules in both directions
            rule_sides = [state.strip() for state in ruleset['rule'].split('->')]
            layer = rule_sides[0][rule_sides[0].index('=')+1].strip()

            states = [[x[0].strip(), x[1].strip()] for x in [rule_side.split(f'={layer}') for rule_side in rule_sides]]
            kappa_rules.append(f"'{layer}: {states[0][0]}-{states[0][1]} to {states[1][0]}-{states[1][1]}'")
            for edge in mln_data['edges'][1][int(layer)-1]:
                v1, v2 = edge[0], edge[1]
                kappa_rules.append(f"// V{v1} - V{v2}")
                site_label = f'{layer}{v1}{v2}'
                kappa_rule = (f'V{v1}(state{{{states[0][0]}}}, l{layer}v{v2}[{site_label}]), V{v2}(state{{{states[0][1]}}}, l{layer}v{v1}[{site_label}]) -> '
                    f'V{v1}(state{{{states[1][0]}}}, l{layer}v{v2}[{site_label}]), V{v2}(state{{{states[1][1]}}}, l{layer}v{v1}[{site_label}]) @ '
                    f"'{ruleset['rate']}'")

                kappa_rules.append(kappa_rule)

        kappa_rules.append('')

    kappa_rules = '\n'.join(kappa_rules)

    return kappa_rules


def parse_language_to_gillespy(STEinFname, OUTFname, mln_data):
    actors, N_actors = mln_data['actors']
    layers, N_layers = mln_data['layers']
    edges, list_split_edges = mln_data['edges']
    
    my_list = []
    tab = '\t'
    
    with open(STEinFname) as f:
        lines = f.readlines()
        columns = [] 

        i = 1
        for line in lines: 
            line = line.strip() # remove leading/trailing white spaces

            if line: 
                if i == 1:
                    columns = [item.strip() for item in line.split(',')]
                    i = i + 1
                else:    
                    d = {}
                    data = [item.strip() for item in line.split(' ')]
                    for index, elem in enumerate(data):
                        d[columns[index]] = data[index]

                    my_list.append(d) # append dictionary to list 
                    
    
    lookingForStates = True
    parsingStates = False
    lookingForParams = False
    parsingParams = False
    lookingForICs = False
    parsingICs = False
    lookingForRules = False
    parsingRules = False
    lookingForViews = False
    parsingViews = False
    lookingForSimOptions = False
    parsingSimOptions = False
    parsingCompleted = False


    N = N_actors ##### NUMBER OF ACTORS IN THE MLN, should be parsed from the MLN file                

    with open(OUTFname, 'w') as out_f:
        list_of_states = []
        list_of_IC = [] 
        rule_counter = 0
        list_of_rules_IDs = []
        list_of_propensities = [] 
        list_of_effects = []         
        list_of_params = [] 
        list_of_views = []

        ### OPTIONS FOR GILLESPIE SIMULATION
        ### number of trajectories/repetitions
        n_rep = 5  ### Default 5
        ### Time horizon
        T_END = 10  ### Default 10

        ##### Manual list of colors for the plot, we can potentially write something else such as a function like the one from the uunet package
        list_of_colors = ['b','g','r','c','m','y','k']
        active_color = 0

        header_string = ('import numpy\n'
                         'import matplotlib.pyplot as plt\n'
                         'from gillespy2.core import (\n'
                         '\tModel,\n'
                         '\tSpecies,\n'
                         '\tReaction,\n'
                         '\tParameter)\n\n'
                         'class Mln_dynamics(Model):\n'
                         '\tdef __init__(self,parameter_values=None):\n'
                         '\t\tModel.__init__(self, name="MLN")\n\n')

        out_f.write(header_string)

        for item in my_list: 
            # parse parameters, species, and reactions
            if lookingForStates == True and item["s1"] == "begin" and item["s2"] == "states": 
                lookingForStates = False
                parsingStates = True

            elif parsingStates == True and item["s1"] != "end":
                #out_f.write(item["s1"]+"\n")
                list_of_states.append(item["s1"])

            elif parsingStates == True and item["s1"] == "end":
                parsingStates = False
                lookingForParams = True

            elif lookingForParams == True and item["s1"] == "begin" and item["s2"] == "parameters":
                parsingParams = True
                lookingForParams = False

            elif parsingParams == True and item["s1"] != "end":
                ### We directly print the paramters into the output file
                #### Desired output: k_c = gillespy2.Parameter(name='k_c',expression=0.05)
                list_of_params.append(item["s1"])
                output = f'\t\t{item["s1"]} = Parameter(name="{item["s1"]}", expression = {item["s3"]})\n'
                out_f.write(output)

            elif parsingParams == True and item["s1"] == "end": 
                parsingParams = False
                lookingForICs = True
                out_f.write("\t\tself.add_parameter([ " )
                for param in list_of_params: 
                    out_f.write( param )
                    if param != list_of_params[-1]:
                        out_f.write(" , ")
                out_f.write(" ] ) \n\n")    

            elif lookingForICs == True and item["s1"] == "begin" and item["s2"] == "IC":
                lookingForICs = False
                parsingICs = True

            elif parsingICs == True and item["s1"] != "end": 
                list_of_IC.append(item["s3"])

            elif parsingICs == True and item["s1"] == "end":
                parsingICs = False
                lookingForRules = True
                #### Printing the species and the ICs 
                #### Desired output: m = gillespy2.Species(name='monomer', initial_value=30)

                for state in list_of_states:
                    for actor in range(N):
                        actor_state = '1' if list_of_IC[actor] == state else '0'
                        output = f'{tab*2}{state}{str(actor)} = Species(name="{state}{str(actor)}", initial_value={actor_state})\n'

                        out_f.write(output)


                ### THERE IS A BETTER WAY TO DO THIS, keep a list of the species names in the generted code i believe can be an option        
                out_f.write("\t\tself.add_species([" )
                for state in list_of_states:
                    for actor in range(N):
                        out_f.write( state+str(actor) )
                        if state == list_of_states[-1] and actor == N-1:
                            continue
                        else:
                            out_f.write( " , ")
                out_f.write("] )\n\n")

            elif lookingForRules == True and item["s1"] == "begin" and item["s2"] == "rules":
                lookingForRules = False
                parsingRules = True    

            elif parsingRules == True and item["s1"] != "end":
                #### PARSING TOWARD REACTIONS
                #### DESIRED RESULT: r_c = gillespy2.Reaction(name="r_creation", rate=k_c, reactants={m:2}, products={d:1})
                #### These first 2 parse rules that talk about layers 1 and 2 with undirected edges
                if item["s2"] == '=1':
    #                 layer_idx = 0 if item["s2"] == '=1' else 1
                    layer_idx = 0
                    for edge in list_split_edges[layer_idx]:
                        output = (f'{tab*2}r_{str(rule_counter)}'
                                  f' = Reaction(\n'
                                  f'{tab*4}name = "r_{str(rule_counter)}",\n'
                                  f'{tab*4}rate = {item["s9"]},\n'
                                  f'{tab*4}reactants = {{{item["s1"]}{str(int(edge[0])-1)}: 1, {item["s3"]}{str(int(edge[1])-1)}: 1}},\n'
                                  f'{tab*4}products = {{{item["s5"]}{str(int(edge[0])-1)}: 1, {item["s7"]}{str(int(edge[1])-1)}: 1}}\n'
                                  f'{tab*3})\n\n')

                        out_f.write(output)
                        rule_counter = rule_counter + 1

                if item["s2"] == '=2':
                    layer_idx = 1
                    for edge in list_split_edges[layer_idx]:
                        output = (f'{tab*2}r_{str(rule_counter)}'
                                  f' = Reaction(\n'
                                  f'{tab*4}name = "r_{str(rule_counter)}",\n'
                                  f'{tab*4}rate = {item["s9"]},\n'
                                  f'{tab*4}reactants = {{{item["s1"]}{str(int(edge[0])-1)}: 1, {item["s3"]}{str(int(edge[1])-1)}: 1}},\n'
                                  f'{tab*4}products = {{{item["s5"]}{str(int(edge[0])-1)}: 1, {item["s7"]}{str(int(edge[1])-1)}: 1}}\n'
                                  f'{tab*3})\n\n')

                        out_f.write(output)
                        rule_counter = rule_counter + 1

                #### Attempt at parsing rules for single nodes
                if item["s2"] == '->': 
                    for actor in actors: 
                        output = (f'{tab*2}r_{str(rule_counter)}'
                                  f' = Reaction(\n'
                                  f'{tab*4}name = "r_{str(rule_counter)}",\n'
                                  f'{tab*4}rate = {item["s5"]},\n'
                                  f'{tab*4}reactants = {{{item["s1"]}{str(int(actor)-1)}: 1}},\n'
                                  f'{tab*4}products = {{{item["s3"]}{str(int(actor)-1)}: 1}}\n'
                                  f'{tab*3})\n\n')

                        out_f.write(output)
                        rule_counter = rule_counter + 1    


            elif parsingRules == True and item["s1"] == "end":
                parsingRules = False
                lookingForViews = True
                out_f.write("\t\tself.add_reaction([")
                for r in range(rule_counter):
                    out_f.write( "r_"+str(r) )
                    if r != rule_counter-1: 
                        out_f.write( " , " )
                out_f.write( "] ) \n\n" )        

            elif lookingForViews == True and item["s1"] == "begin" and item["s2"] == "views":
                lookingForViews = False
                parsingViews = True 

            elif parsingViews == True and item["s1"] != "end":
                list_of_views.append(item["s1"])

            elif parsingViews == True and item["s1"] == "end":
                parsingViews = False
                lookingForSimOptions = True

            elif lookingForSimOptions == True and item["s1"] == "begin" and item["s2"] == "simOptions":
                lookingForSimOptions = False
                parsingSimOptions = True

            elif parsingSimOptions == True and item["s1"] != "end":
                if item["s1"] == "n":
                    n_rep = int(item["s3"])
                if item["s1"] == "t":
                    T_END = int(item["s3"])

            elif parsingSimOptions == True and item["s1"] == "end":
                parsingSimOptions = False
                parsingCompleted = True
                

        footer_string = (f'{tab*2}self.timespan(numpy.linspace(0, {str(T_END)}, {str(T_END*20)}))\n\n'
                         'def run_sim(model):\n'
                         f'{tab}results = model.run(number_of_trajectories={str(n_rep)})\n'
                         f'{tab}trajectory = results.average_ensemble()\n'
                         f'{tab}plt.figure()\n')
        out_f.write(footer_string)
        trajectories = [[] for i in range(len(list_of_views))]
        out_f.write(f'{tab}trajectories = {str(trajectories)}\n')
        out_f.write(f'{tab}for i in range(len(trajectory["{list_of_views[0]}0"])):\n')
        list_of_colors = ['b','g','r','c','m','y','k']
        active_color = 0
        for view in list_of_views:
            idx = list_of_views.index(view)
            s = f'{tab*2}trajectories[{idx}].append('
            for actor in actors:
                s += f'trajectory["{view}{int(actor)-1}"][i]'
                if actor != actors[-1]:
                    s += ' + '
            s += ')\n'
            out_f.write(f'{s}')
        
        for view in list_of_views:
            idx = list_of_views.index(view)
            out_f.write(f'{tab}plt.plot(trajectory["time"], trajectories[{idx}], "{list_of_colors[idx]}", label="{view}")\n')
    
        out_f.write(f'{tab}plt.legend(loc="upper right")\n')
        out_f.write(f'{tab}plt.annotate(text=f"n = {str(n_rep)}", xy=(0.1, 0.9), xycoords="axes fraction")\n')

        out_f.write(f"{tab}plt.show()")









