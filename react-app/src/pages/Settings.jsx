import { useState } from "react";
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';
import Select from 'react-select';

export default function Settings() {   

    const mileageSteps = [
        0, 100, 500, 5000, 10000, 15000, 20000, 25000, 30000,
        35000, 40000, 45000, 50000, 60000, 70000, 80000, 90000,
        100000, 125000, 150000, 200000
    ];

    const priceSteps = [
        0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000,
        5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000,
        11000, 12000, 13000, 14000, 15000, 16000, 17000, 18000, 19000, 20000,
        22500, 25000, 27500, 30000, 35000, 40000, 45000, 50000,
        55000, 60000, 65000, 70000, 75000, 100000, 250000, 500000, 1000000, 2000000
    ];

    const radiusOptions = ['1','5','10','15','20','25','30','35','40','45','50','55','60','70','80','90','100','200'];

    const makeOptions = [
        "Abarth", "AC", "AK", "Alfa Romeo", "Allard", "Alpine", "Alvis", "Ariel", "Aston Martin",
        "Audi", "Austin", "BAC", "Beauford", "Bentley", "BMW", "Bramwith", "Bugatti", "BYD", "Cadillac", // and more...
    ];

    const [formData, setFormData] = useState({
        postcode: "",
        radius: 50,
        make: [],
        priceIndex: [0, priceSteps.length - 1],
        mileageIndex: [0, mileageSteps.length - 1],
        transmission: []
    });

    const handleMakeChange = (selected) => {
        setFormData((prev) => ({ ...prev, make: selected.map((s) => s.value) }));
    };

    const handleTransmissionChange = (selected) => {
        setFormData((prev) => ({ ...prev, transmission: selected.map((s) => s.value) }));
    };

    return (
        <form className="space-y-4">
        {/* Postcode */}
        <div>
            <label>Postcode</label>
            <input
            type="text"
            name="postcode"
            maxLength={8}
            className="border rounded p-2 w-full"
            value={formData.postcode}
            onChange={(e) => setFormData({ ...formData, postcode: e.target.value })}
            />
        </div>

        {/* Radius */}
        <div>
            <label>Radius: {formData.radius} miles</label>
            <Slider
            min={0}
            max={radiusOptions.length - 1}
            step={1}
            value={radiusOptions.indexOf(formData.radius.toString())}
            marks={radiusOptions.reduce((acc, val, idx) => {
                if (idx % 4 === 0) acc[idx] = val;
                return acc;
            }, {})}
            onChange={(i) => setFormData({ ...formData, radius: parseInt(radiusOptions[i]) })}
            />
        </div>

        {/* Make */}
        <div>
            <label>Make</label>
            <Select
            isMulti
            options={makeOptions.map((m) => ({ label: m, value: m }))}
            onChange={handleMakeChange}
            />
        </div>

        {/* Price */}
        <div>
            <label>Price Range: £{priceSteps[formData.priceIndex[0]]} – £{priceSteps[formData.priceIndex[1]]}</label>
            <Slider
            range
            min={0}
            max={priceSteps.length - 1}
            step={1}
            value={formData.priceIndex}
            allowCross={false}
            onChange={(value) => setFormData({ ...formData, priceIndex: value })}
            />
        </div>

        {/* Mileage */}
        <div>
            <label>Mileage Range: {mileageSteps[formData.mileageIndex[0]]} – {mileageSteps[formData.mileageIndex[1]]} mi</label>
            <Slider
            range
            min={0}
            max={mileageSteps.length - 1}
            step={1}
            value={formData.mileageIndex}
            allowCross={false}
            onChange={(value) => setFormData({ ...formData, mileageIndex: value })}
            />
        </div>

        {/* Transmission */}
        <div>
            <label>Transmission</label>
            <Select
            isMulti
            options={["Automatic", "Manual"].map((t) => ({ label: t, value: t }))}
            onChange={handleTransmissionChange}
            />
        </div>

        {/* Debug Preview */}
        <div className="bg-gray-100 p-4 text-sm">
            {/* <pre>{JSON.stringify({
            ...formData,
            // price: [priceSteps[formData.priceIndex[0]], priceSteps[formData.priceIndex[1]]],
            // mileage: [mileageSteps[formData.mileageIndex[0]], mileageSteps[formData.mileageIndex[1]]],
            }, null, 2)}</pre> */}
        </div>        



        </form>

        

    );
}
