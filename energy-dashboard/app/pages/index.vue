<template>
    <div class="Top">
        <img class="logo" src="/img/logo.png" alt="Logo">
        <div class="Title">ENERGY NETWORK SIMULATOR</div>
        <div class="Title_y">2026</div>
        <select name="" id="" class="Select">
            <option>Scénario 1</option>
            <option>Scénario 2</option>
            <option>Scénario 3</option>
            <option>Scénario 4</option>
        </select>
        <div class="Button_div">
            <button class="Button_play" onclick="startSimulation()">
                <svg viewBox="0 0 24 24" fill="white" width="15" height="15">
                    <polygon points="5,3 19,12 5,21 5,3"/>
                </svg>
            </button>
            <button class="Button_stop" onclick="stopSimulation()">
                <svg viewBox="0 0 24 24" fill="Red" width="20" height="20">
                    <rect x="8" y="8" width="9" height="9" rx="1"/>
                </svg>
            </button>
        </div>
            <div class="Loader" id="Loader"></div>
            <div class="Simu_ready" id="Simu_ready"> Simulation Ready !</div>





            <button class="Export">Export</button>
    </div>
    


    <div class="Mid">
        <div class="Main_content"> 
            <div class="Schemas">
                <div class="Schemas_header">
                    Simulation
                </div>
                <div class="Schemas_content">
                    <div class="Img_header">
                                <select name="" id="imageSelector" class="Img_selection_header" onchange="showImage()">
                                    <option value="schema exemple 1">Schema Exemple 1</option>
                                    <option value="schema exemple 2">Schema Exemple 2</option>
                                </select>
                    </div>
                    <div class="Img_content" id="imageDisplay"><img src="/img/schema exemple 1.png" alt="Sélection" class="schema_1"></div>
                </div>
            </div>
            <div class="Kpi-list">
                <div class="Kpi"></div>
                <div class="Kpi"></div>
                <div class="Kpi"></div>
                <div class="Kpi"></div>
            </div>
        </div>
        <div class="Right_panel">
        </div>
    </div>


<div class="Bottom">
        <div class="Blue_circle"></div>
         <a class="Data_ref" href="https://developer.dataplatform.knmi.nl/apis" target="_blank">DATA REFERENCE: KNMI Data Platform</a>
    </div>
</template>
