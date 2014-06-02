define([], function() {

return {
    title       : 'Pie chart',
    library     : 'nvd3.js',
    category    : 'Area charts',
    tag         : 'svg',
    use_panels  : true,
    columns : {
        label : {
            title       : 'Labels',
            is_label    : true
        },
        y : {
            title       : 'Values'
        }
    },
    
    settings : {
        show_legend : {
            title       : 'Show legend',
            info        : 'Would you like to add a legend?',
            type        : 'select',
            init        : 'false',
            data        : [
                {
                    label   : 'Yes',
                    value   : 'true'
                },
                {
                    label   : 'No',
                    value   : 'false'
                }
            ]
        },
       
        donut_ratio : {
            title       : 'Donut ratio',
            info        : 'Determine how large the donut hole will be.',
            type        : 'select',
            init        : '0.5',
            data        : [
                {
                    label   : '50%',
                    value   : '0.5'
                },
                {
                    label   : '25%',
                    value   : '0.25'
                },
                {
                    label   : '10%',
                    value   : '0.10'
                },
                {
                    label   : '0%',
                    value   : '0'
                }
            ]
        },
       
        label_separator : {
            type        : 'separator',
            title       : 'Label settings'
        },
       
        label_type : {
            title       : 'Donut label',
            info        : 'What would you like to show for each slice?',
            type        : 'select',
            init        : 'percent',
            data        : [
                {
                    label   : '-- Nothing --',
                    value   : 'hide',
                    hide    : 'label_outside'
                },
                {
                    label   : 'Label column',
                    value   : 'key',
                    show    : 'label_outside'
                },
                {
                    label   : 'Value column',
                    value   : 'value',
                    show    : 'label_outside'
                },
                {
                    label   : 'Percentage',
                    value   : 'percent',
                    show    : 'label_outside'
                }
            ],
        },

        label_outside : {
            title       : 'Show outside',
            info        : 'Would you like to show labels outside the donut?',
            type        : 'select',
            init        : 'false',
            data        : [
                {
                    label   : 'Yes',
                    value   : 'true'
                },
                {
                    label   : 'No',
                    value   : 'false'
                }
            ]
        }
    }
};

});